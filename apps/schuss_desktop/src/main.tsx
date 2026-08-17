import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import * as Tooltip from "@radix-ui/react-tooltip";
import { App } from "./App";
import "./styles/tokens.css";
import "./styles/global.css";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("Schuss desktop root is unavailable");
}

createRoot(root).render(
  <StrictMode>
    <Tooltip.Provider delayDuration={350} skipDelayDuration={150}>
      <App />
    </Tooltip.Provider>
  </StrictMode>,
);
