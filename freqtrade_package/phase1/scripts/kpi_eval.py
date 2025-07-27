#!/usr/bin/env python3
# KPIs: Sharpe>1, Win%>50, MaxDD>=-0.40, PF>=1.0
import argparse, glob, json, math, datetime as dt
from pathlib import Path
def load_trades(p):
    d=json.load(open(p,encoding='utf-8'))
    return d['trades'] if isinstance(d,dict) and 'trades'in d else d
def kpi(trades):
    daily={}; w=l=0; gg=gl=0.0
    for t in trades:
        s=t.get('close_date') or t.get('sell_date') or t.get('close_time')
        if isinstance(s,str):
            try: d=dt.datetime.fromisoformat(s.replace('Z','')).date()
            except: d=dt.datetime.utcfromtimestamp(0).date()
        else:
            d=dt.datetime.utcfromtimestamp((s or 0)/1000 if (s or 0)>10**12 else (s or 0)).date()
        pr=float(t.get('profit_ratio',0)); pa=float(t.get('profit_abs',0))
        daily[d]=daily.get(d,0)+pr
        (w:=w+1, gg:=gg+abs(pa)) if pr>0 else ((l:=l+1, gl:=gl+abs(pa)) if pr<0 else None)
    if not daily: return dict(sh=0,win=0,mdd=0,pf=0,n=0)
    rets=[v for _,v in sorted(daily.items())]
    eq=1.0; peak=1.0; mdd=0.0
    for r in rets: eq*=1+r; peak=max(peak,eq); mdd=min(mdd,eq/peak-1.0)
    mu=sum(rets)/len(rets); var=sum((x-mu)**2 for x in rets)/len(rets) if len(rets)>1 else 0.0
    std=var**0.5; sh=(mu/std*(365**0.5)) if std>0 else 0.0
    n=w+l; win=w/n if n>0 else 0.0; pf=(gg/gl) if gl>0 else (float('inf') if gg>0 else 0.0)
    return dict(sh=sh,win=win,mdd=mdd,pf=pf,n=n)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--glob',default='user_data/backtest_results/*.json')
    ap.add_argument('--sharpe-min',type=float,default=1.0)
    ap.add_argument('--win-min',type=float,default=0.50)
    ap.add_argument('--mdd-min',type=float,default=-0.40)
    ap.add_argument('--pf-min',type=float,default=1.0)
    a=ap.parse_args(); paths=sorted(glob.glob(a.glob)); ok=True
    for p in paths:
        k=kpi(load_trades(p)); passed=(k['sh']>a.sharpe_min and k['win']>a.win_min and k['mdd']>=a.mdd_min and k['pf']>=a.pf_min)
        print(f"[KPI] {Path(p).name}: Sharpe={k['sh']:.2f}, Win%={k['win']*100:.1f}%, PF={k['pf']:.2f}, MaxDD={k['mdd']*100:.1f}% -> {'PASS' if passed else 'FAIL'}")
        ok=ok and passed
    if ok: open('READY_TO_RUN','w',encoding='utf-8').write('ok'); print('[KPI] PASS'); exit(0)
    print('[KPI] FAIL'); exit(1)
if __name__=='__main__': main()
