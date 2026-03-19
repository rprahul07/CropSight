import { useState } from "react";
import UploadArea from "@/components/upload/UploadArea";
import SummaryCards from "@/components/dashboard/SummaryCards";
import MapView from "@/components/dashboard/MapView";
import ZoneAnalysis from "@/components/dashboard/ZoneAnalysis";
import { AnalyzeResponse } from "@/types/analysis";
import { Upload as UploadIcon } from "lucide-react";

const UploadPage = () => {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [activeZoneId, setActiveZoneId] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground flex items-center gap-2">
          <UploadIcon className="h-6 w-6 text-primary" />
          Upload & Analyze
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload crop imagery for AI-powered vegetation analysis
        </p>
      </div>

      <div className="max-w-2xl">
        <UploadArea onAnalysisComplete={setAnalysis} />
      </div>

      {analysis && (
        <>
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
        </>
      )}
    </div>
  );
};

export default UploadPage;
