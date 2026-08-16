import React, { useState } from "react";
import {
  analyzeBusiness,
  getMemories,
  getMultimodalRequirements,
  getPlugins,
  planResearch,
  runAgent,
  runIntelligence,
  uploadDocument,
  type BusinessAnalysis,
  type IntelligenceResult,
  type Memory,
} from "../lib/api";

type WorkspaceMode =
  | "agents"
  | "intelligence"
  | "research"
  | "business"
  | "documents"
  | "memory"
  | "multimodal"
  | "plugins";

interface WorkspaceProps {
  mode: WorkspaceMode;
}

function ResultBlock({ value }: { value: unknown }) {
  if (value == null) return null;

  return (
    <pre className="workspace-result">
      {typeof value === "string"
        ? value
        : JSON.stringify(value, null, 2)}
    </pre>
  );
}

export default function Workspace({ mode }: WorkspaceProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setResult(null);
    setError(null);
  };

  const execute = async () => {
    const value = input.trim();
    if (!value || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      switch (mode) {
        case "agents":
          setResult(await runAgent(value));
          break;

        case "intelligence":
          setResult(await runIntelligence(value));
          break;

        case "research":
          setResult(await planResearch(value));
          break;

        case "business":
          setResult(await analyzeBusiness(value));
          break;

        case "documents":
          setError("Choose a document below to upload.");
          break;

        case "memory": {
          const memories: Memory[] = await getMemories();
          setResult(memories);
          break;
        }

        case "multimodal":
          setResult(await getMultimodalRequirements(value));
          break;

        case "plugins":
          setResult(await getPlugins());
          break;
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Falcon could not complete the request."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDocument = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      setResult(await uploadDocument(file));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Document upload failed."
      );
    } finally {
      setLoading(false);
      event.target.value = "";
    }
  };

  const titles: Record<WorkspaceMode, string> = {
    agents: "Agents",
    intelligence: "Intelligence",
    research: "Research",
    business: "Business Analysis",
    documents: "Documents",
    memory: "Memory",
    multimodal: "Multimodal",
    plugins: "Plugins",
  };

  const descriptions: Record<WorkspaceMode, string> = {
    agents: "Give Falcon a goal and let the agent orchestration layer prepare and execute it.",
    intelligence: "Run Falcon's unified cognition pipeline: understand, plan, execute, reflect and verify.",
    research: "Prepare a structured research strategy for a question.",
    business: "Analyze a business problem using Falcon's business-analysis capability.",
    documents: "Upload documents into Falcon's knowledge pipeline.",
    memory: "Inspect the memories currently associated with your Falcon account.",
    multimodal: "Inspect requirements for image, audio, video and other media workflows.",
    plugins: "Inspect Falcon's currently registered plugins.",
  };

  const placeholders: Record<WorkspaceMode, string> = {
    agents: "Describe the goal you want Falcon to accomplish...",
    intelligence: "What should Falcon reason through?",
    research: "What do you want Falcon to research?",
    business: "Describe the business problem...",
    documents: "",
    memory: "",
    multimodal: "Enter a media type, for example: image, audio, video...",
    plugins: "",
  };

  return (
    <section className="workspace">
      <div className="workspace-header">
        <div>
          <div className="workspace-eyebrow">FALCON WORKSPACE</div>
          <h1>{titles[mode]}</h1>
          <p>{descriptions[mode]}</p>
        </div>

        <button
          className="workspace-reset"
          onClick={reset}
          disabled={loading}
        >
          Clear
        </button>
      </div>

      {mode === "documents" ? (
        <div className="workspace-card">
          <h2>Upload a document</h2>
          <p>
            Falcon will store the document and send its contents through the
            existing indexing pipeline.
          </p>

          <label className="workspace-upload">
            <span>
              {loading ? "Uploading..." : "Choose a file"}
            </span>
            <input
              type="file"
              onChange={handleDocument}
              disabled={loading}
            />
          </label>
        </div>
      ) : (
        <div className="workspace-card">
          {(mode === "agents" ||
            mode === "intelligence" ||
            mode === "research" ||
            mode === "business" ||
            mode === "multimodal") && (
            <>
              <textarea
                className="workspace-input"
                rows={6}
                placeholder={placeholders[mode]}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                disabled={loading}
              />

              <button
                className="workspace-run"
                onClick={execute}
                disabled={loading || !input.trim()}
              >
                {loading ? "Running Falcon..." : "Run Falcon"}
              </button>
            </>
          )}

          {(mode === "memory" || mode === "plugins") && (
            <button
              className="workspace-run"
              onClick={execute}
              disabled={loading}
            >
              {loading ? "Loading..." : "Load"}
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="workspace-error">
          {error}
        </div>
      )}

      {result !== null && (
        <div className="workspace-card">
          <div className="workspace-result-title">
            Falcon result
          </div>
          <ResultBlock value={result} />
        </div>
      )}
    </section>
  );
}