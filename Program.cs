// TokenContinue.cs
//
// Requires: LLamaSharp NuGet package (and a backend, e.g. LLamaSharp.Backend.Cpu)
//   dotnet add package LLamaSharp
//   dotnet add package LLamaSharp.Backend.Cpu   // or .Cuda12, .MacMetal, etc.

using LLama;
using LLama.Common;
using LLama.Native;
using LLama.Sampling;

// ── Configuration ────────────────────────────────────────────────────────────
const string ModelPath = @"C:\AIModels\Llama-3.2-3B-Instruct-f16.gguf";   // path to your GGUF model file
const string InputPath = "C:\\Users\\User\\Documents\\smith-inquiry-161.txt";    // path to the input .txt file
const int TargetLength = 1024;          // context length to test around (swept TargetLength±2)

// Context must fit the warmup + 5 decode tokens
const int ModelContextSize = TargetLength + 64;

if (!File.Exists(ModelPath)) { Console.Error.WriteLine($"Error: model file not found: {ModelPath}"); return; }
if (!File.Exists(InputPath)) { Console.Error.WriteLine($"Error: input file not found: {InputPath}"); return; }

// ── Load model ───────────────────────────────────────────────────────────────
Console.Error.WriteLine($"Loading model: {ModelPath}");

var modelParams = new ModelParams(ModelPath)
{
    ContextSize = (uint)ModelContextSize,
    GpuLayerCount = 0,
    UseMemoryLock = false,
    BatchSize = 8192
};

using var model = LLamaWeights.LoadFromFile(modelParams);

// ── Tokenize ──────────────────────────────────────────────────────────────────
LLamaToken[] sourceTokens;
{
    using var tempContext = model.CreateContext(modelParams);
    var allTokens = tempContext.Tokenize(File.ReadAllText(InputPath), addBos: true);
    Console.Error.WriteLine($"File tokenized to {allTokens.Length} tokens");

    int needed = ModelContextSize;
    if (allTokens.Length < needed)
    {
        Console.Error.WriteLine($"Error: need at least {needed} tokens but only got {allTokens.Length}");
        return;
    }

    sourceTokens = allTokens[..needed];
}

using var context = model.CreateContext(modelParams);
using var pipeline = new DefaultSamplingPipeline();
var decoder = new StreamingTokenDecoder(context);

// ── Warmup: fill KV cache with the first (TargetLength-3) tokens ─────────────
int warmupCount = TargetLength - 65;
Console.Error.WriteLine($"Warming up KV cache with {warmupCount} tokens...");

var warmupBatch = new LLamaBatch();
for (int i = 0; i < warmupCount; i++)
    warmupBatch.Add(sourceTokens[i], i, LLamaSeqId.Zero, logits: false);

var warmupResult = context.Decode(warmupBatch);
if (warmupResult != DecodeResult.Ok)
{
    Console.Error.WriteLine($"Warmup decode failed: {warmupResult}");
    return;
}

// ── 5s pause — start your profiling software now ─────────────────────────────
Console.Error.WriteLine("Warmup complete. Start your profiling software. Resuming in 5s...");
await Task.Delay(TimeSpan.FromSeconds(5));

// ── 5 measured decodes: positions (TargetLength-3) through (TargetLength+1) ──
// Each decode sees one more token of context than the last, sweeping ±2 around TargetLength.
Console.Error.WriteLine("Running measured decodes...");

for (int i = 0; i < 128; i++)
{
    int pos = warmupCount + i;
    int testLength = pos + 1; // context length seen by this decode

    var batch = new LLamaBatch();
    batch.Add(sourceTokens[pos], pos, LLamaSeqId.Zero, logits: true);

    var result = context.Decode(batch);
    if (result != DecodeResult.Ok)
    {
        Console.Error.WriteLine($"Decode failed at pos {pos}: {result}");
        return;
    }

    var newToken = pipeline.Sample(context, 0);
    decoder.Add(newToken);
    Console.WriteLine($"contextLength={testLength}: '{decoder.Read()}'");

    pipeline.Reset();
}