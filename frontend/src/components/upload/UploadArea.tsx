import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, Image as ImageIcon, X, Loader2, Sprout } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { analyzeImage } from "@/services/api";
import { AnalyzeResponse } from "@/types/analysis";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

const ANALYSIS_STEPS = [
  "Analyzing vegetation indices...",
  "Extracting geolocation metadata...",
  "Detecting crop stress zones...",
  "Generating health map...",
];

interface UploadAreaProps {
  onAnalysisComplete: (data: AnalyzeResponse) => void;
  fieldId?: string;
}

const UploadArea = ({ onAnalysisComplete, fieldId }: UploadAreaProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) {
      const f = accepted[0];
      setFile(f);
      setPreview(URL.createObjectURL(f));
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/jpeg": [], "image/png": [] },
    maxFiles: 1,
    disabled: analyzing,
  });

  const handleAnalyze = async () => {
    if (!file) return;
    setAnalyzing(true);
    setCurrentStep(0);

    const interval = setInterval(() => {
      setCurrentStep((prev) => Math.min(prev + 1, ANALYSIS_STEPS.length - 1));
    }, 1000);

    try {
      const data = await analyzeImage(file, fieldId);
      clearInterval(interval);
      onAnalysisComplete(data);
      toast.success("Analysis complete — results ready!");
    } catch {
      clearInterval(interval);
      toast.error("Analysis failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setCurrentStep(0);
  };

  if (analyzing) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="card-elevated p-10 flex flex-col items-center justify-center min-h-[400px] gap-6"
      >
        <div className="relative">
          <div className="h-16 w-16 rounded-full border-4 border-muted border-t-primary animate-spin" />
          <Sprout className="h-6 w-6 text-primary absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
        </div>
        <div className="space-y-3 text-center">
          {ANALYSIS_STEPS.map((step, i) => (
            <motion.p
              key={step}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: i <= currentStep ? 1 : 0.3, x: 0 }}
              transition={{ delay: i * 0.2, duration: 0.3 }}
              className={`text-sm font-medium ${i <= currentStep ? "text-foreground" : "text-muted-foreground"}`}
            >
              {i < currentStep ? "✓" : i === currentStep ? "⏳" : "○"} {step}
            </motion.p>
          ))}
        </div>
        <div className="w-48 h-1.5 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary rounded-full"
            initial={{ width: "0%" }}
            animate={{ width: `${((currentStep + 1) / ANALYSIS_STEPS.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
      </motion.div>
    );
  }

  return (
    <div className="card-elevated p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Upload Crop Image</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Upload a drone or smartphone image for vegetation stress analysis
        </p>
      </div>

      {!preview ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200 ${
            isDragActive
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/50 hover:bg-muted/50"
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm font-medium text-foreground">
            {isDragActive ? "Drop your image here" : "Drag & drop your crop image"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">JPG, JPEG, PNG accepted</p>
        </div>
      ) : (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-4">
          <div className="relative rounded-xl overflow-hidden border border-border">
            <img src={preview} alt="Crop preview" className="w-full max-h-80 object-cover" />
            <button
              onClick={handleReset}
              className="absolute top-3 right-3 bg-card/80 backdrop-blur-sm rounded-full p-1.5 hover:bg-card transition-colors"
            >
              <X className="h-4 w-4 text-foreground" />
            </button>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ImageIcon className="h-4 w-4" />
            <span className="truncate">{file?.name}</span>
            <span className="ml-auto">{file ? (file.size / 1024 / 1024).toFixed(2) : 0} MB</span>
          </div>
        </motion.div>
      )}

      <div className="flex gap-3">
        <Button onClick={handleAnalyze} disabled={!file} className="flex-1 btn-glow gap-2">
          <Sprout className="h-4 w-4" />
          Analyze Crop
        </Button>
        {preview && (
          <Button variant="outline" onClick={handleReset}>
            Upload New Image
          </Button>
        )}
      </div>
    </div>
  );
};

export default UploadArea;
