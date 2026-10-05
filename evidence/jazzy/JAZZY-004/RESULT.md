# 制御環境での結果

- 実行commit: `a3508eb9c35630ad9e2d32ef2f7f6b0d49aa174d`。clean checkout、導入済みartifactとソースのhash一致を確認。
- 状態: FIXED_IN_CONTROLLED_ENVIRONMENT。push後はPUSHED_CANDIDATE。手動GUI・実機は未確認。
- context終了とpublishの競合を再現する4テストがPASS。生きたcontextのRCLErrorを再送出する2条件も含む。
- 既存のgeometry 5テストと合わせて9件PASS。テスト間で残るTcl callbackはfixtureで解放し、複数Tkを同じテストプロセスに作る際の干渉を避けた。
- CycloneDDS / ドメイン100: 通信・入力・timeout・再開19条件PASS。Joy実測19.9910Hz、Twist実測100.2051Hz。
- CycloneDDS・Fast DDS両方のSIGINT終了で、両ノードが正常終了。例外・起動した子PIDの残存なし。
- Fast DDSの最新runではtopic discoveryが15秒でタイムアウト。過去の診断runではJoy/Twist受信が成功しており、通信が安定しない原因は未確認。
- GUI表示を仮想ディスプレイ全画面のPNGで確認。ユーザーの画面と手動操作は未確認。
- 各runのmanifestにPID・コマンド・cwd・runtime hash・実際のRMW/domainを保存。Fast DDS通信の成功とは扱わず、mainへ昇格しない。
