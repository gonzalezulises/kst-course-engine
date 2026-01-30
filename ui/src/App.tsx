import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CourseProvider } from "./context/CourseContext";
import { Shell } from "./components/layout/Shell";
import { InfoPage } from "./components/pages/InfoPage";
import { ValidatePage } from "./components/pages/ValidatePage";
import { PathsPage } from "./components/pages/PathsPage";
import { SimulatePage } from "./components/pages/SimulatePage";
import { ExportPage } from "./components/pages/ExportPage";
import { AssessPage } from "./components/pages/AssessPage";

export default function App() {
  return (
    <BrowserRouter>
      <CourseProvider>
        <Shell>
          <Routes>
            <Route path="/" element={<InfoPage />} />
            <Route path="/validate" element={<ValidatePage />} />
            <Route path="/paths" element={<PathsPage />} />
            <Route path="/simulate" element={<SimulatePage />} />
            <Route path="/export" element={<ExportPage />} />
            <Route path="/assess" element={<AssessPage />} />
          </Routes>
        </Shell>
      </CourseProvider>
    </BrowserRouter>
  );
}
