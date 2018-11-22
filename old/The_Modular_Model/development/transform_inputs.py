outputs_dir = 'uc_inputs/'
GEN=pd.read_csv(os.path.join(outputs_dir,'gen.tab'), sep='\t')
LINE=pd.read_csv(os.path.join(outputs_dir,'line.tab'), sep='\t')
LOADZONES=pd.read_csv(os.path.join(outputs_dir,'load_zones.tab'), sep='\t')
#TIMEPOINTS = pd.read_csv(os.path.join(outputs_dir,'timepoints.tab'), sep='\t')
ZONEDEMAND =pd.read_csv(os.path.join(outputs_dir,'zone_demand.tab'), sep='\t')
VCF =pd.read_csv(os.path.join(outputs_dir,'variable_capacity_factors.tab'), sep='\t')
VWC =pd.read_csv(os.path.join(outputs_dir,'variable_water_cost.tab'), sep='\t')

TIMEPOINT_DF = pd.DataFrame()
TIMEPOINT_DF['TIMEPOINT']= range(1,25)

GEN.to_csv(os.path.join(outputs_dir,'gen.csv'), sep=',')
LINE.to_csv(os.path.join(outputs_dir,'line.csv'), sep=',',index=False)
LOADZONES.to_csv(os.path.join(outputs_dir,'load_zones.csv'),sep=',', index=False)
TIMEPOINT_DF.to_csv(os.path.join(outputs_dir,'timepoints.csv'), sep=',',index=False)
ZONEDEMAND.to_csv(os.path.join(outputs_dir,'zone_demand.csv'), sep=',',index=False)
VCF.to_csv(os.path.join(outputs_dir,'variable_capacity_factors.csv'), sep=',',index=False)
VWC.to_csv(os.path.join(outputs_dir,'variable_water_cost.csv'), sep=',',index=False)
