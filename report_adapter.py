"""Audit the restricted adapter records and generate a Chinese progress note."""
import hashlib
import json
from pathlib import Path
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from route_adapter import certify,sha256_json,UnsupportedSchedule
from validation import validate

ROOT=Path(__file__).resolve().parent
FOLDER=ROOT/'results/adapter_2026-11-01'

def main():
    summary=json.loads((FOLDER/'summary.json').read_text())
    protocol=summary['protocol'];reference_path=ROOT/'results/three_qubit_2026-10-31/summary.json'
    assert hashlib.sha256(reference_path.read_bytes()).hexdigest()==protocol['reference_summary_sha256']
    references=json.loads(reference_path.read_text())['records']
    assert summary['accepted_requests']==72 and summary['unique_physical_circuits']==8 and summary['new_monte_carlo_shots']==0
    assert len(list((FOLDER/'source_routes').glob('*.json')))==18
    assert len(list((FOLDER/'requests').glob('*.json')))==72
    for n,h in protocol['source_files_sha256'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
    for item in summary['accepted']:
        request=json.loads((FOLDER/'requests'/(item['case']+'.json')).read_text())
        stored=json.loads((FOLDER/'certificates'/(item['case']+'.json')).read_text())
        current=certify(request);current['physical_check_key']=item['physical_check_key']
        assert current==stored and item['request_sha256']==sha256_json(request)
    for key,physical in summary['physical_checks'].items():
        assert physical==json.loads((FOLDER/'physical_checks'/(key+'.json')).read_text())
        row=next(r for r in references if r['name']==physical['reference_name'])
        for field in ['ideal_circuit_sha256','circuit_sha256','model_id','decoder_id']:assert physical[field]==row[field]
        assert physical['reference_shots']==row['shots']==100000
        assert physical['reference_failures_any']==row['failures_any']
        assert physical['reference_wilson95']==[row['wilson95_low'],row['wilson95_high']]
        assert physical['block_footprint_verification']['matched_actual_backend_graph']
        assert physical['physical_validation']['all_eight_signed_inputs_passed'] and physical['shortest_graphlike_error']==3
    negative=json.loads((FOLDER/'negative_cases.json').read_text())
    for item in negative:
        try:certify(item['request'])
        except UnsupportedSchedule as error:assert error.code==item['expected_code']
        else:raise AssertionError('Negative case accepted')
        if item['name'].startswith('legal_'):
            q=item['request'];validate(q['gates'],q['architecture'],q['mapping'],q['steps'])
    assert summary['unique_referenced_shots']==sum(p['reference_shots'] for p in summary['physical_checks'].values())==800000
    tests=(FOLDER/'tests.log').read_text();test_count=int(re.search(r'(\d+) passed',tests).group(1))
    audit={'passed':True,'source_routing_configurations':18,'requests_checked':72,'unique_full_circuit_references':8,
           'new_monte_carlo_shots':0,'unique_existing_shots_referenced':800000,'explicit_rejections':len(negative),
           'local_test_count':test_count,'checks':['source hashes','recomputed certificates','exact ideal/noisy circuit hash references',
                     'reference counts/CI/model/decoder','stored backend footprint and physical validation','negative cases'],
           'scope':'Record reconciliation; physical circuits were generated and validated by the runner, no Monte Carlo run by this audit.'}
    (FOLDER/'record_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    # Use a real source-router result for the diagram; source and block units remain distinct.
    req=json.loads((FOLDER/'requests/span3_original_s1_z_idle0.json').read_text());cert=certify(req)
    fig,axes=plt.subplots(1,2,figsize=(12,5.2),gridspec_kw={'width_ratios':[1.6,1]})
    ax=axes[0];width=req['architecture']['width'];height=req['architecture']['height']
    reserved=set(v for c in cert['corridors'] for v in c['reserved_source_vertices'])
    ax.scatter([v%width for v in reserved],[v//width for v in reserved],marker='s',s=85,color='#DDDDDD',zorder=1)
    for item in cert['corridors']:
        for field,style,color in [('chosen_source_vertices','--','#666666'),('normalized_source_vertices','-','#111111')]:
            path=item[field];ax.plot([v%width for v in path],[v//width for v in path],style,color=color,lw=2,zorder=2)
    for q,v in req['mapping']:
        ax.scatter(v%width,v//width,marker='s',s=210,color='#111111',zorder=3)
        ax.text(v%width,v//width-.4,f'q{q}',ha='center',fontsize=11)
    ax.set(title='Source grid: full corridors reserved',xlabel='Source grid x',ylabel='Source grid y',
           xlim=(-.5,width-.5),ylim=(height-.5,-.5),xticks=range(0,width,2),yticks=range(height),aspect='equal')
    ax.grid(alpha=.15)
    ax.legend(handles=[Line2D([],[],color='#666666',ls='--',label='Router-chosen path'),
                       Line2D([],[],color='#111111',label='Normalized path')],loc='upper center',bbox_to_anchor=(.5,-.18),ncol=2,frameon=False)
    ax=axes[1];data=set(map(tuple,cert['logical_block_xy']));ancilla=set()
    for item in cert['physical_footprints']:ancilla.update(map(tuple,item['ancilla_blocks']))
    ax.scatter([x for x,y in ancilla],[y for x,y in ancilla],marker='s',s=550,color='#CCCCCC',edgecolors='#555555')
    for i,(x,y) in enumerate(cert['logical_block_xy']):
        ax.scatter(x,y,marker='s',s=550,color='#111111');ax.text(x,y,f'q{i}',ha='center',va='center',color='white',fontsize=11)
    ax.set(title='Backend block footprint (union over time)',xlabel='TQEC block x',ylabel='TQEC block y',
           xlim=(-.7,6.7),ylim=(2.7,-.7),xticks=range(7),yticks=range(3),aspect='equal')
    ax.grid(alpha=.15);ax.text(.5,-.4,'Gray: ancilla blocks\nBlack: live logical patches',transform=ax.transAxes,ha='center',va='top',fontsize=10)
    fig.suptitle('Restricted span-3 embedding: corridor normalization, not edge-by-edge execution',fontsize=12)
    fig.tight_layout();fig.savefig(ROOT/'docs/figures/adapter_corridor_embedding.png',dpi=180,bbox_inches='tight');plt.close(fig)
    report=f'''# 2026-11-01：可拒絕不支援輸入的受限 route-to-circuit 介面

## 今天新增了什麼

已把實際 DASCOT 路由輸出，接到已驗證的三位元物理電路。介面先檢查來源路由合法性，再檢查指定幾何、控制／目標邊界、完整保留走廊、ancilla footprint 與時間政策，最後才產生 Stim 電路及可追溯的 certificate。不符合條件時會回傳明確拒絕原因。

今天驗證的是**轉譯與合成介面**，不是新的路由演算法優勢。來源採原作者 original、我們的 one-step 與 two-step，各 3 個 seeds、2 個宣告的 layout，共 18 組路由；再加 X/Z 與額外 storage 0/1，形成 72 份請求。

| 本次檢查 | 結果與正確解讀 |
|---|---|
| 實際 router 來源 | 18 組，使用自訂的指定走廊 layout；不是 18 個 application benchmarks |
| 支援輸入 | 72／72 份通過；是上述模板生成的請求，不代表任意路由覆蓋率 |
| 不同物理電路 | 8 個；逐一通過 8 組輸入符號、3 種 final logical fault、graphlike distance=3 |
| 不支援範例 | 6 組均拒絕，包含「抽象合法、但模板不支援」的繞路與邊界 |
| 本地測試 | {test_count} 項通過；遠端 CI 看本次提交的 Actions |
| 新 Monte Carlo shots | **0**；沒有把既有校準重新算成新抽樣 |
| 引用完整電路校準 | 8 個不同電路各 100,000 shots，合計既有 800,000 shots；不是 72×100,000 個獨立樣本 |

## 為什麼需要這一層

之前的三位元電路直接由程式指定幾何。今天多了來源端：`gates → mapping → routed paths → 檢查與正規化 → physical circuit`。這樣才能知道某份路由是否真的能對應到物理模型，而不是看到路徑有幾個 hops，就直接查一個錯誤率。

目前支援 `CNOT(a,b) → CNOT(b,c)`，三個不同邏輯位元；支援 d=3、X/Z basis、span 1/3、額外 storage 0/1。邏輯 ID 可重新命名，但資料位置、路由方向、資源與時間規則必須符合明確 profile。每個 CNOT 都在自己的 source step，沒有並行模板。

## 重要的工程選擇：保留整條走廊，允許在走廊內正規化

原 router 可能在同一個空走廊裡選不同的轉彎位置。物理 backend 則有固定的 CNOT block template。因此介面要求整個兩列走廊都沒有資料／magic-state 障礙，並且該步只有這個 gate，才把來源路徑改成模板使用的 canonical 路徑；改前改後都通過獨立 abstract validator。

![來源走廊與物理 block footprint](../figures/adapter_corridor_embedding.png)

這是一份**保留邏輯操作與順序的受限合成合約**，沒有聲稱逐邊執行原細路徑。左圖的 source grid 與右圖的 TQEC block 是不同單位；bridge span 從宣告的資料位置 embedding 決定，沒有從路徑長度猜測。

完整走廊的保留量比單一細路徑大，因此未來擴充並行操作時，不能只看細路徑互不重疊，就假設物理模板也能並行。目前介面直接拒絕不符合串行模板的排程。

## 時間與存活狀態如何對應

來源的 2 個 routing steps 不直接等於 2 個 block 或 TICK。請求必須明確提供 physical timing policy：每個 CNOT 佔 3 個 block-z；額外 storage 是另外提供的 0／1 個 block。

| 額外 storage | 第一個 CNOT 的 block-z | 第二個 CNOT 的 block-z | 所有位元存活區間 | 編譯後 TICKs |
|---|---|---|---|---:|
| 0 | [0,3] | [3,6] | [0,6] | 146 |
| 1 | [0,3] | [4,7] | [0,7] | 167 |

q0 完成第一個 gate 後仍保留、q2 在第二個 gate 前也已存在；這些 memory 沒有被省略。Certificate 的 ancilla／data block footprint 會和實際 backend graph 比對，共同起訖時間也會核對。Clifford 的 observable／frame 記帳沿用已驗證的 correlation flows；沒有擴充到含 T gate 的動態 feed-forward。

## 如何引用既有錯誤率，避免把 proxy 當實測

對 8 個不同 backend 電路，同時核對 ideal 與完整 noisy circuit 的 SHA-256、三個 observables、d、p、noise model 及 decoder。全部相符後才引用 10/31 的完整電路紀錄；沒有把孤立 gadget 的 survival 相乘，也沒有再次抽樣。

例如 Z / span 1 / extra storage 1，引用的是 `three_z_d3_span1_idle1_p0.001_N100000`：7377／100000，7.377%，95% Wilson CI [7.217%, 7.541%]。條件是 TQEC uniform-depolarizing circuit noise、p=0.001、普通 uncorrelated PyMatching MWPM；原始 counts、seed、batch、ideal/noisy `.stim` 與 `.dem` 仍在 10/31 的凍結資料與快照中。這是**相同完整電路的校準重用**，不是今天新增的錯誤率改善。

## 誠實量化支援範圍

另對 Phase 1 的 540 份完整 routing records 做相容性檢查：**0／540** 符合目前二-gate motif；這些 records 來自 20 個 input/layout 定義，不能當成 540 個獨立 workloads。結果沒有裁切成小片段來提高覆蓋率。

這表示介面已在指定的小模板上跑通，但目前不能拿它替 Phase 1 大電路宣稱完整物理結果。這兩個 gates 也共享中間位元，沒有並行選擇，所以三種來源方法產生相同物理電路時，不構成演算法優勢比較。

下一步優先擴大可支援 workload 與不同合法排程，並把保留 footprint 與等待政策納入來源端；再做同一邏輯工作、相同資源條件的完整電路比較。Scheduler **mu 保持 0**。

## 如何看紀錄與重現

- `results/adapter_2026-11-01/source_routes/`：來源程式、layout、method、seed 與實際路由。
- `requests/` 與 `certificates/`：72 份輸入和逐份驗證結果、走廊、正規化路徑與時間／footprint。
- `physical_checks/`：8 個完整電路的 hash 比對、邏輯驗證與引用的 counts／CI。
- `negative_cases.json`、`phase1_coverage.json`：拒絕案例與完整 workload 覆蓋率。
- `protocol.json`、`record_audit.json`、`tests.log`：規則、來源 hash、結果核對與測試。

```bash
python -m pytest tests -q
python restore_results.py
python report_adapter.py
python route_adapter.py results/adapter_2026-11-01/requests/span1_original_s1_z_idle1.json --output results_fresh/compiled
python -c "from pathlib import Path; import run_adapter_validation as r; r.FOLDER=Path('results_fresh/adapter'); r.main()"
```

`route_adapter.py` 會產生 `ideal.stim` 和 `certificate.json`；已有 output 目錄會拒絕覆寫。最後一行把整份驗證寫入新的 `results_fresh/adapter`，不會改動凍結結果；該資料夾也必須尚未存在。Report 預設仍讀取凍結紀錄，不會自動把 fresh validation 當成原研究。這次原始紀錄另存於 `archives/adapter_2026-11-01.zip`。

TQEC 的原 CNOT graph、composition 與 physical compiler 仍屬原作者；本次新增是來源路由介面、可拒絕的 synthesis contract、幾何／時間／footprint 檢查與資料追溯。引用來源固定於 TQEC commit `50fa2210597632a79bd266b56a5fb8d9b00747bb` 與 wisq commit `97c12a5e22cf16e37288c60a0a5735c58c6fe8ca`。
'''
    (ROOT/'docs/updates/2026-11-01.md').write_text(report)
    print(json.dumps(audit))

if __name__=='__main__':main()
