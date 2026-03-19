  -- Create 'fields' table
  CREATE TABLE fields (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Create 'scans' table
  CREATE TABLE scans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    field_id UUID REFERENCES fields(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    image_url TEXT,
    overlay_url TEXT,
    healthy_pct NUMERIC,
    moderate_pct NUMERIC,
    severe_pct NUMERIC,
    total_zones INTEGER
  );

  -- Create 'zones' table
  CREATE TABLE zones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    zone_index INTEGER,
    severity TEXT,
    health_score NUMERIC,
    area NUMERIC,
    issue TEXT,
    recommendation TEXT,
    geo_coordinates JSONB
  );

  -- Set Row Level Security (RLS)
  ALTER TABLE fields ENABLE ROW LEVEL SECURITY;
  ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
  ALTER TABLE zones ENABLE ROW LEVEL SECURITY;

  -- Create Policies for RLS
  CREATE POLICY "Users can manage their own fields"
  ON fields FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

  CREATE POLICY "Users can manage their own scans"
  ON scans FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

  CREATE POLICY "Users can manage their own zones"
  ON zones FOR ALL
  TO authenticated
  USING (
    scan_id IN (SELECT id FROM scans WHERE user_id = auth.uid())
  )
  WITH CHECK (
    scan_id IN (SELECT id FROM scans WHERE user_id = auth.uid())
  );
