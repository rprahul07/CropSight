import { useState } from "react";
import { motion } from "framer-motion";
import UploadArea from "@/components/upload/UploadArea";
import SummaryCards from "@/components/dashboard/SummaryCards";
import MapView from "@/components/dashboard/MapView";
import ZoneAnalysis from "@/components/dashboard/ZoneAnalysis";
import { AnalyzeResponse } from "@/types/analysis";
import { Sprout } from "lucide-react";

const Dashboard = () => {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [activeZoneId, setActiveZoneId] = useState<number | null>(null);

  if (!analysis) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-foreground flex items-center gap-2">
            <Sprout className="h-6 w-6 text-primary" />
            Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Upload a crop image to begin analysis
          </p>
        </div>
        <UploadArea onAnalysisComplete={setAnalysis} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground flex items-center gap-2">
            <Sprout className="h-6 w-6 text-primary" />
            Analysis Results
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {analysis.summary.total_zones} zones detected across your field
          </p>
        </div>
        <button
          onClick={() => setAnalysis(null)}
          className="text-sm text-primary font-medium hover:underline"
        >
          New Analysis
        </button>
      </div>

      <SummaryCards summary={analysis.summary} />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3">
          <MapView 
            geo={analysis.geo} 
            zones={analysis.zones} 
            activeZoneId={activeZoneId}
            mapImage={analysis.map}
          />
        </div>
        <div className="lg:col-span-2">
          <ZoneAnalysis
            zones={analysis.zones}
            activeZoneId={activeZoneId}
            onZoneSelect={setActiveZoneId}
          />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
