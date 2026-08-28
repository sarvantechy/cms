import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import PortalApp from "./PortalApp";
import "./PortalApp.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <PortalApp />
    </BrowserRouter>
  </StrictMode>,
);
