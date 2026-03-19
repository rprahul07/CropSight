import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Radar, Cpu, Activity, Clock, Sprout, AlertCircle, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { cropSightApi } from "@/services/api";
import { supabase } from "@/lib/supabase";

interface IngestFrame {
  id: string;
  image_url: string;
  timestamp: string;
  device_id: string;
  status: string;
}

export default function DroneFeed() {
  const [frames, setFrames] = useState<IngestFrame[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [lastPoll, setLastPoll] = useState<Date>(new Date());

  const fetchPendingFrames = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // In a real app we might filter by user_id if we attached it during ingest, 
      // but for simulation we just fetch all scans from the user's field.
      // Easiest is to just fetch the common Scans and filter for 'pending_analysis'
      const fieldsObj = await cropSightApi.getFields(user.id);
      const fieldId = fieldsObj.fields?.[0]?.id;
      
      if (fieldId) {
        const data = await cropSightApi.getHistoricalScans(fieldId);
        const pending = (data.scans || []).filter((s: any) => s.status === "pending_analysis");
        setFrames(pending);
      }
    } catch (err) {
      console.error("Failed to poll frames", err);
    } finally {
      setLoading(false);
      setLastPoll(new Date());
    }
  };

  useEffect(() => {
    fetchPendingFrames();
    const interval = setInterval(fetchPendingFrames, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (id: string) => {
    setAnalyzingId(id);
    toast.loading("AI Engine processing frame...", { id: "analyze-frame" });
    try {
      await cropSightApi.analyzeExistingScan(id);
      toast.success("Analysis complete! Metadata updated.", { id: "analyze-frame" });
      setFrames(prev => prev.filter(f => f.id !== id)); // Remove from pending list
    } catch (err) {
      toast.error("Analysis failed. Check your backend logs.", { id: "analyze-frame" });
    } finally {
      setAnalyzingId(null);
    }
  };

  const latestFrame = frames[0];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header with Animation */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-card p-6 rounded-2xl border border-border shadow-sm">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
            <div className="relative">
              <Radar className="h-8 w-8 text-primary animate-pulse" />
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-card animate-ping" />
            </div>
            Drone Live Feed
          </h1>
          <p className="text-muted-foreground mt-1 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-500" />
            Machine-to-Machine Ingestion Pipeline Active
          </p>
        </div>
        
        <div className="flex items-center gap-6 text-sm">
          <div className="text-center px-4 border-r border-border">
            <p className="text-muted-foreground">Pending Frames</p>
            <p className="text-xl font-bold text-primary">{frames.length}</p>
          </div>
          <div className="text-center px-4">
            <p className="text-muted-foreground">Last Sync</p>
            <p className="font-medium">{lastPoll.toLocaleTimeString()}</p>
          </div>
          <button 
             onClick={() => { setLoading(true); fetchPendingFrames(); }}
             className="p-2 hover:bg-muted rounded-full transition-colors"
          >
             <RefreshCw className={`w-5 h-5 text-muted-foreground ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Main Feed View */}
        <div className="lg:col-span-2 space-y-6">
          <div className="relative aspect-video rounded-3xl overflow-hidden bg-muted border-4 border-card shadow-2xl group">
             <AnimatePresence mode="wait">
                {latestFrame ? (
                  <motion.div
                    key={latestFrame.id}
                    initial={{ opacity: 0, scale: 1.05 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.5 }}
                    className="h-full w-full"
                  >
                    <img 
                      src={latestFrame.image_url} 
                      className="w-full h-full object-cover" 
                      alt="Latest Drone Frame" 
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex flex-col justify-end p-8">
                       <div className="flex justify-between items-end">
                          <div>
                             <p className="text-white/70 text-sm font-medium">LATEST CAPTURE</p>
                             <h2 className="text-white text-2xl font-bold flex items-center gap-2">
                               {latestFrame.device_id} <span className="text-white/40 font-mono text-sm">{latestFrame.id.slice(0, 8)}</span>
                             </h2>
                             <p className="text-white/60 text-sm mt-1 flex items-center gap-1">
                               <Clock className="w-3 h-3" /> {new Date(latestFrame.timestamp).toLocaleString()}
                             </p>
                          </div>
                          <button
                            disabled={!!analyzingId}
                            onClick={() => handleAnalyze(latestFrame.id)}
                            className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3 rounded-2xl font-bold text-lg shadow-lg hover:shadow-primary/20 transition-all flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {analyzingId === latestFrame.id ? (
                               <RefreshCw className="w-5 h-5 animate-spin" />
                            ) : (
                               <Cpu className="w-5 h-5" />
                            )}
                            Analyze This Frame
                          </button>
                       </div>
                    </div>
                  </motion.div>
                ) : (
                  <div className="h-full w-full flex flex-col items-center justify-center space-y-4 p-12 text-center">
                    <div className="p-6 bg-background/50 rounded-full">
                       <Radar className="w-12 h-12 text-muted-foreground animate-spin-slow" />
                    </div>
                    <div>
                       <h3 className="text-xl font-semibold">Waiting for telemetry...</h3>
                       <p className="text-muted-foreground mt-1 max-w-xs mx-auto">
                         The system is ready to receive drone frames. Run your simulation script or connect a device.
                       </p>
                    </div>
                  </div>
                )}
             </AnimatePresence>
             
             {/* HUD elements */}
             <div className="absolute top-6 left-6 flex gap-2">
                <div className="px-3 py-1 bg-black/40 backdrop-blur-md border border-white/20 rounded-full text-white text-xs font-mono uppercase tracking-widest flex items-center gap-2">
                   <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                   Rec 4K
                </div>
                <div className="px-3 py-1 bg-black/40 backdrop-blur-md border border-white/20 rounded-full text-white text-xs font-mono flex items-center gap-2">
                   ISO 100 | f/2.8 | 1/500
                </div>
             </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
             <div className="card-elevated p-4 bg-primary/5 border-primary/10">
                <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Alt</p>
                <p className="text-lg font-bold">120m</p>
             </div>
             <div className="card-elevated p-4 bg-emerald-500/5 border-emerald-500/10">
                <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Signals</p>
                <p className="text-lg font-bold text-emerald-600">Stable</p>
             </div>
             <div className="card-elevated p-4 bg-amber-500/5 border-amber-500/10">
                <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">Mode</p>
                <p className="text-lg font-bold">Auto</p>
             </div>
             <div className="card-elevated p-4 bg-blue-500/5 border-blue-500/10">
                <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">FOV</p>
                <p className="text-lg font-bold text-blue-600">84°</p>
             </div>
          </div>
        </div>

        {/* Sidebar: Queue */}
        <div className="space-y-4 max-h-[700px] overflow-hidden flex flex-col">
           <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <Clock className="w-5 h-5 text-primary" />
                Ingestion Queue
              </h3>
              <span className="text-[10px] text-muted-foreground uppercase font-bold bg-muted px-2 py-1 rounded">Latest 10</span>
           </div>
           
           <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
              <AnimatePresence initial={false}>
                {frames.length > 0 ? (
                   frames.map((frame, idx) => (
                    <motion.div
                      key={frame.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, scale: 0.9 }}
                      transition={{ delay: idx * 0.05 }}
                      whileHover={{ scale: 1.02 }}
                      className="bg-card border border-border rounded-xl p-3 flex items-center gap-3 cursor-pointer group hover:border-primary/40 transition-all shadow-sm"
                      onClick={() => handleAnalyze(frame.id)}
                    >
                      <div className="w-16 h-16 rounded-lg overflow-hidden bg-muted flex-shrink-0 border border-border shadow-inner relative">
                         <img src={frame.image_url} className="w-full h-full object-cover" />
                         {analyzingId === frame.id && (
                           <div className="absolute inset-0 bg-primary/40 flex items-center justify-center">
                              <RefreshCw className="w-4 h-4 text-white animate-spin" />
                           </div>
                         )}
                      </div>
                      <div className="flex-1 min-w-0">
                         <div className="flex items-center gap-1.5">
                            <p className="text-xs font-bold truncate uppercase tracking-tighter">{frame.device_id}</p>
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                         </div>
                         <p className="text-[10px] text-muted-foreground mt-0.5">{new Date(frame.timestamp).toLocaleTimeString()}</p>
                         <button className="text-[10px] font-bold text-primary opacity-0 group-hover:opacity-100 transition-opacity mt-1 flex items-center gap-1 uppercase">
                           <Sprout className="w-3 h-3" /> Quick Analyze
                         </button>
                      </div>
                    </motion.div>
                   ))
                ) : (
                   <div className="p-8 border-2 border-dashed border-border rounded-2xl flex flex-col items-center justify-center text-center opacity-40">
                      <AlertCircle className="w-8 h-8 mb-2" />
                      <p className="text-sm font-medium">Queue Empty</p>
                   </div>
                )}
              </AnimatePresence>
           </div>
        </div>

      </div>
    </div>
  );
}
