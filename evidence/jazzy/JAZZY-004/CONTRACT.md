# JAZZY-004: context終了とpublishの競合

- 対象: ROS 2 Jazzy。Fast DDSの診断で発見。通信不成立の原因とは分離して扱う。
- 観測: `8513fc7`のSIGINT終了で、GUI spin threadのpublishが`publisher's context is invalid`を送出。プロセスexit 0だけでは正常終了の根拠にならない。
- 失敗証拠: `../diagnostics/fastdds-8513fc7/`。実行commit・実体hashとログを保存。
- 原因仮説: signalによるcontextの非同期終了が実行中timer callbackと競合する。KeyboardInterrupt/ExternalShutdownExceptionの捕捉だけではこのRCLErrorを扱えない。
- 原因を示す値: 実際のnodeでcontextを終了後にtimer publishを呼び、同じRCLErrorを再現する。
- 変更許可: 両ノードのmainのspin例外処理と必要なimportだけ。
- 変更禁止: publisher callbackの入力・速度・timeout・QoS、ROS/DDSのvendorコード、Fast DDSの環境設定。
- 合格条件: context終了後のpublish競合がmainから未捕捉で出ない。contextが生きている間のRCLErrorは再送出し、隠さない。
- 回帰条件: CycloneDDS・ドメイン100の通信・19条件・正常なSIGINT終了、GUI close callback、既存geometryテスト5件。
- Fast DDS通信は診断条件。これを修正済みと呼ばない。手動GUI・実機は未確認のままmainへ昇格しない。
