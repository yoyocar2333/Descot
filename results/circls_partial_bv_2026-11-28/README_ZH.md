# 完整BV：CircLS partial-output PPM control

完整解釋見docs/updates/2026-11-28-circls-partial-bv.md。主要32編譯、9最短plans×2政策和各8種signed inputs；全部原兩輸出與旗標保留，2jointPPM。18主條件同一noisy電路。

0new shots，counts/CI=null，mu=0。完整source/plan/ideal/noisy/DEM hashes在逐筆records；用restore_results.py還原後執行verify_circls_partial_control.py。65實際native物理編譯的完整帳包含32preflight+1探索；見preflight_accounting.json。

Native T1_rounds=12僅表示含量測的moments；QEC rounds=null、Stim TICK=73。原TQEC模板／noise／lifetime不同，不作錯誤率或幾何效率勝負。
