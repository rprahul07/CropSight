import { motion } from "framer-motion";
import { Layers, Leaf, AlertTriangle, AlertOctagon } from "lucide-react";
import { Summary } from "@/types/analysis";

interface SummaryCardsProps {
  summary: Summary;
}

const SummaryCards = ({ summary }: SummaryCardsProps) => {
  const cards = [
    {
      label: "Total Zones",
      value: summary.total_zones,
      icon: Layers,
      color: "text-foreground",
      bg: "bg-muted",
    },
    {
      label: "Healthy",
      value: `${summary.healthy}%`,
      icon: Leaf,
      color: "text-success",
      bg: "bg-success/10",
    },
    {
      label: "Moderate",
      value: `${summary.moderate}%`,
      icon: AlertTriangle,
      color: "text-warning",
      bg: "bg-warning/10",
    },
    {
      label: "Severe",
      value: `${summary.severe}%`,
      icon: AlertOctagon,
      color: "text-destructive",
      bg: "bg-destructive/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1, duration: 0.3 }}
          className="card-elevated p-5 flex items-start gap-4"
        >
          <div className={`p-2.5 rounded-xl ${card.bg}`}>
            <card.icon className={`h-5 w-5 ${card.color}`} />
          </div>
          <div>
            <p className={`text-2xl font-semibold ${card.color}`}>{card.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{card.label}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default SummaryCards;
