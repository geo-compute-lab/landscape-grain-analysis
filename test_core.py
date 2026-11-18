import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grain_statistics import progressive_uf, sequential_mk, pettitt_test, uf_ub_candidates
from landscape_methods import area_errors,regional_V,retention_screen,corridor_is_continuous
from run_retention import evaluate
from run_recommendation import choose_grain
from run_statistics import load_metrics


def test_area_error_V_definition():
    err = area_errors([100,50],[90,55])
    assert np.allclose(err,[-10,10])
    assert regional_V(err) == pytest.approx(10)
    v, fail = retention_screen(err,False)
    assert fail['regional_V'] and not fail['class_area_error']
    assert v == pytest.approx(10)


def test_progressive_MK_two_observations_correct_variance():
    # Pair increase count after two observations is 1, expected 0.5,
    # variance 0.25 => UF[1] = 1.0 (some earlier transcripts used 7/72).
    uf = progressive_uf([1,2,3,4])
    assert uf[0] == 0.0
    assert uf[1] == pytest.approx(1.0)
    assert uf[-1] > uf[1]
    uf, ub = sequential_mk([1,2,3,4,5])
    assert len(uf)==len(ub)==5
    assert np.isfinite(ub).all()


def test_pettitt_approx_and_ties():
    grains=np.arange(1,21)
    seq=np.r_[np.zeros(10),np.ones(10)]
    pet=pettitt_test(seq,grains)
    assert pet['grain_m']==10
    assert pet['K']==100
    assert 0<pet['p_approx']<0.01
    assert 0 <= pettitt_test(np.ones(10), np.arange(10))['p_approx']<=1


def test_corridor_four_neighbour_binary():
    grid=np.array([[1,1,1],[0,0,0]], dtype=bool)
    mask=np.ones_like(grid, bool)
    assert corridor_is_continuous(grid,mask,(0,0),(0,2))
    grid[0,1]=False
    assert not corridor_is_continuous(grid,mask,(0,0),(0,2))


def test_operational_retention_first_failure():
    rows=[]
    for size, area2, broken in [(5,50,False),(10,48,False),(15,45,True),(20,40,True)]:
        for c,base,after in [('A',100,100),('B',50,area2)]:
            rows.append({'SIZE':size,'class':c,'reference_area':base,
                         'raster_area':after,'corridor_discontinuous':broken})
    result,limit=evaluate(pd.DataFrame(rows))
    assert limit==15.0
    assert result['any_criterion'].tolist()==[False,False,True,True]


def test_recommendation_cluster_with_interval_tolerance():
    rows=[]
    for metric, grain in [('NP',50),('PD',50),('ENN_MN',50),('PLADJ',50),('COHESION',48),('AI',50),('MESH',62)]:
        rows.append({'metric':metric,'pettitt_grain_m':grain,'pettitt_p_approx':0.001})
    grain, ranking=choose_grain(pd.DataFrame(rows),60,step=2,agreement=5)
    assert grain==50
    assert ranking.iloc[0]['support_n']==6
    grain, ranking=choose_grain(pd.DataFrame(rows),45,step=2,agreement=4)
    assert grain is None


def test_aliases_sheet_and_filter(tmp_path):
    data=pd.DataFrame({'LID':['HAIKOU']*5,'SIZE':[5,10,15,20,25],
                       'NP':[8,7,6,3,2],'ENNN':[4,5,6,7,8],'ESH':[1,2,3,4,5]})
    file=tmp_path/'temp.xlsx'
    data.to_excel(file,index=False,sheet_name='HAIKOU')
    groups=load_metrics(file,sheet='HAIKOU',area='HAIKOU')
    assert 'ENN_MN' in groups[0][1].columns and 'MESH' in groups[0][1].columns
