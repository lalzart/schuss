import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@xyflow/react/dist/style.css";

import App from "./App";
import { PrototypeErrorBoundary } from "./components/PrototypeErrorBoundary";
import "./styles.css";

const root = document.getElementById("root");
if (!root) throw new Error("Machine prototype failed closed: #root is missing");

createRoot(root).render(
  <StrictMode>
    <PrototypeErrorBoundary>
      <App />
    </PrototypeErrorBoundary>
  </StrictMode>,
);
