import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("photocatDesktop", {
  runtime: "electron",
  processingBoundary: "python",
});
