import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Sprout, Activity, Layout, Eye, TrendingUp, AlertTriangle } from "lucide-react";
import { cropSightApi } from "@/services/api";
import { supabase } from "@/lib/supabase";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
          const data = await cropSightApi.getDashboardStats(user.id);
          setStats(data);
        }
      } catch (err) {
        console.error("Failed to fetch dashboard stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
     return (
       <div className="flex flex-col items-center justify-center p-24 space-y-4">
         <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
         <p className="text-muted-foreground animate-pulse">Loading intelligence...</p>
       </div>
     );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        staggerChildren: 0.15 
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0, scale: 0.95 },
    visible: { y: 0, opacity: 1, scale: 1, transition: { stiffness: 100, damping: 12 } }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      <motion.div variants={itemVariants}>
        <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
          <Activity className="h-8 w-8 text-primary" />
          Analytics Dashboard
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">
          Welcome back. Here's the current state of your monitored farmlands.
        </p>
      </motion.div>

      {stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-8">
          <motion.div variants={itemVariants} className="card-elevated p-6 bg-gradient-to-br from-background to-primary/5 hover:to-primary/10 transition-colors border-l-4 border-l-primary relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
               <Eye className="w-24 h-24" />
            </div>
            <div className="flex justify-between items-start relative z-10">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Scans</p>
                <h3 className="text-4xl font-bold mt-2">{stats.total_scans}</h3>
              </div>
              <div className="p-3 bg-primary/10 rounded-xl shadow-sm">
                <Eye className="w-6 h-6 text-primary" />
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="card-elevated p-6 bg-gradient-to-br from-background to-emerald-500/5 hover:to-emerald-500/10 transition-colors border-l-4 border-l-emerald-500 relative overflow-hidden group">
             <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
               <Sprout className="w-24 h-24" />
             </div>
             <div className="flex justify-between items-start relative z-10">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg. Healthy %</p>
                <h3 className="text-4xl font-bold mt-2 text-emerald-600">{stats.avg_healthy_pct}%</h3>
              </div>
              <div className="p-3 bg-emerald-100 rounded-xl shadow-sm">
                <Sprout className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="card-elevated p-6 bg-gradient-to-br from-background to-amber-500/5 hover:to-amber-500/10 transition-colors border-l-4 border-l-amber-500 relative overflow-hidden group">
             <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
               <AlertTriangle className="w-24 h-24" />
             </div>
             <div className="flex justify-between items-start relative z-10">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg. Moderate Risk</p>
                <h3 className="text-4xl font-bold mt-2 text-amber-600">{stats.avg_moderate_pct}%</h3>
              </div>
              <div className="p-3 bg-amber-100 rounded-xl shadow-sm">
                <AlertTriangle className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="card-elevated p-6 bg-gradient-to-br from-background to-red-500/5 hover:to-red-500/10 transition-colors border-l-4 border-l-red-500 relative overflow-hidden group">
             <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
               <TrendingUp className="w-24 h-24" />
             </div>
             <div className="flex justify-between items-start relative z-10">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Avg. Severe Damage</p>
                <h3 className="text-4xl font-bold mt-2 text-red-600">{stats.avg_severe_pct}%</h3>
              </div>
              <div className="p-3 bg-red-100 rounded-xl shadow-sm">
                <TrendingUp className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </motion.div>
        </div>
      ) : (
        <motion.div variants={itemVariants} className="text-center p-12 bg-card rounded-xl border border-border mt-8">
           <Sprout className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
           <p className="text-lg text-muted-foreground">No data available yet. Please complete a scan.</p>
        </motion.div>
      )}

      {stats && stats.total_scans > 0 && (
        <motion.div variants={itemVariants} className="mt-8 rounded-2xl overflow-hidden shadow-lg border border-border">
          <div className="p-8 bg-card text-card-foreground">
             <h3 className="text-2xl font-semibold mb-6 text-foreground flex items-center gap-2">
               <Layout className="w-6 h-6 text-primary" />
               Farm Health Insights
             </h3>
             <div className="space-y-4">
                <motion.div 
                   whileHover={{ x: 10 }}
                   className="flex items-center gap-4 p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20"
                >
                   <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                   <span className="text-lg">Based on <strong>{stats.total_scans}</strong> scans, your average healthy crop coverage is <strong className="text-emerald-600">{stats.avg_healthy_pct}%</strong>.</span>
                </motion.div>
                
                {stats.avg_severe_pct > 0 && (
                  <motion.div 
                     whileHover={{ x: 10 }}
                     className="flex items-center gap-4 p-4 rounded-lg bg-red-500/5 border border-red-500/20"
                  >
                     <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>
                     <span className="text-lg">Critical: An average of <strong className="text-red-600">{stats.avg_severe_pct}%</strong> of your field shows severe anomalies requiring immediate attention.</span>
                  </motion.div>
                )}
                
                <motion.div 
                   whileHover={{ x: 10 }}
                   className="flex items-center gap-4 p-4 rounded-lg bg-primary/5 border border-primary/20"
                >
                   <div className="w-3 h-3 rounded-full bg-primary shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                   <span className="text-lg">Total detection zones analyzed across history: <strong>{stats.total_zones}</strong>.</span>
                </motion.div>
             </div>
          </div>
        </motion.div>
      )}

    </motion.div>
  );
}
