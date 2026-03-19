import { motion } from "framer-motion";
import { Zone } from "@/types/analysis";
import { Badge } from "@/components/ui/badge";

interface ZoneAnalysisProps {
  zones: Zone[];
  activeZoneId: number | null;
  onZoneSelect: (id: number) => void;
}

const severityVariant: Record<string, string> = {
  HIGH: "bg-destructive/10 text-destructive border-destructive/20",
  MODERATE: "bg-warning/10 text-warning border-warning/20",
  LOW: "bg-success/10 text-success border-success/20",
};

const ZoneAnalysis = ({ zones, activeZoneId, onZoneSelect }: ZoneAnalysisProps) => {
  return (
    <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
      <h3 className="text-sm font-semibold text-foreground px-1">Zone Analysis</h3>
      {zones.map((zone, i) => (
        <motion.div
          key={zone.zone_id}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.08, duration: 0.3 }}
          onClick={() => onZoneSelect(zone.zone_id)}
          className={`card-elevated p-4 cursor-pointer transition-all duration-200 ${
            activeZoneId === zone.zone_id ? "ring-2 ring-primary/40 shadow-lg" : ""
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-foreground">Zone {zone.zone_id}</span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${severityVariant[zone.severity]}`}>
              {zone.severity}
            </span>
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Health Score</span>
              <span className="font-medium text-foreground">{zone.health_score.toFixed(2)}</span>
            </div>
            <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${zone.health_score * 100}%`,
                  backgroundColor:
                    zone.severity === "HIGH" ? "hsl(var(--destructive))" :
                    zone.severity === "MODERATE" ? "hsl(var(--warning))" :
                    "hsl(var(--success))",
                }}
              />
            </div>
            <p className="text-xs text-foreground font-medium mt-2">{zone.issue}</p>
            <p className="text-xs text-muted-foreground">{zone.recommendation}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default ZoneAnalysis;
