import matplotlib.pyplot as plt
import pandas as pd
import os
from matplotlib.backends.backend_pdf import PdfPages
import datetime
import numpy as np


outputs_dir = 'uc_outputs/'
GEN_COMMIT=pd.read_csv(os.path.join(outputs_dir,'gen_commit.tab'), sep='\t')
GEN_START_UP=pd.read_csv(os.path.join(outputs_dir,'gen_start_up.tab'), sep='\t' )
GEN_SHUT_DOWN=pd.read_csv(os.path.join(outputs_dir,'gen_shut_down.tab'), sep='\t' )
GEN_PG = pd.read_csv(os.path.join(outputs_dir,'gen_pg.tab'), sep='\t')
Timepoints = GEN_COMMIT['TIMEPOINT']
Columns = list(GEN_COMMIT)
Gens = [gen for gen in Columns if gen != 'TIMEPOINT']
Simplified_Gens = [gen for gen in Gens if ('\xf3' not in gen)]
Simplified_Gens = [gen for gen in Simplified_Gens if ('\xed' not in gen)]
Simplified_Gens = [gen for gen in Simplified_Gens if ('\xe9' not in gen)]
Simplified_Gens = [gen for gen in Simplified_Gens if ('\xf1' not in gen)]
Simplified_Gens = [gen for gen in Simplified_Gens if ('\xfa' not in gen)]
Simplified_Gens = [gen for gen in Simplified_Gens if ('\xd1' not in gen)]
Simplified_Gens = [gen for gen in Simplified_Gens if ('\xe1' not in gen)]

for gen in Simplified_Gens:
    fig,ax1=plt.subplots()
    color='tab:red'
    ax1.set_xlabel('Timepoint (t)')
    ax1.set_ylabel('PG (MW)', color=color)
    ax1.plot(Timepoints, GEN_PG[gen], color=color)
    
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Commit Status', color=color)
    ax2.plot(Timepoints, GEN_COMMIT[gen], color=color)
    ax2.plot(Timepoints, GEN_START_UP[gen], color='aqua')
    ax2.plot(Timepoints, GEN_SHUT_DOWN[gen], color='fuchsia')
    fig.tight_layout()
    plt.title(gen)

    
    plt.show()
    plt.close()

