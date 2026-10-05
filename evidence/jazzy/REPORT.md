# virtual_joy Jazzyブランチの移行・検証記録

2026-10-05、Ubuntu 24.04 / ROS 2 Jazzyで確認しました。
Humble版main `ab3a96f49c4a5e7c17e6e21d49673487c2fecfe6`から新しい`jazzy`ブランチを作成しました。
mainへのmerge・更新は行っていません。現在の段階はPUSHED_CANDIDATEで、ユーザーの実利用環境での確認は未実施です。

## 変更

| 問題 | 原因と変更 | 記録 |
|---|---|---|
| SIGINT終了時例外 | 終了済みcontextへの二重shutdownとspin例外。try_shutdownとmainの終了処理を変更 | [JAZZY-001](JAZZY-001/RESULT.md) |
| Joy停止後の横移動残存 | timeoutでlinear.yがゼロにならない。既存閾値のままゼロ化を追加 | [JAZZY-002](JAZZY-002/RESULT.md) |
| rosdep依存解決失敗 | 解決できないament_python buildtool_dependを削除。build_typeとruntime依存を維持 | [JAZZY-003](JAZZY-003/RESULT.md) |
| context終了とpublishの競合 | 終了済みcontextのRCLErrorをmainで扱う。生きたcontextの異常は再送出 | [JAZZY-004](JAZZY-004/RESULT.md) |

各問題の失敗・再現テストを先にcommit/pushし、remote反映を確認してから修正しました。
各修正の制御環境での成功checkpointをpushしてから次の問題へ進めました。
READMEはUbuntu 24.04、jazzyブランチのclone、依存解決、Jazzy overlay、ドメイン100・CycloneDDSの起動手順へ変更しました。
入力割り当て・速度値・timeout閾値・GUI描画・トピックは変更していません。

## 確認結果

- rosdep check / installとcolcon build: exit 0。両entrypointと両launchの引数を確認。
- 最新runtime: `a3508eb9c35630ad9e2d32ef2f7f6b0d49aa174d`。それ以降の変更はREADME・検証記録です。
- geometry 5件＋shutdown race 4件: 9件PASS。
- CycloneDDS: 4.001793秒でJoy 80件・Twist 401件、約19.99Hz / 100.21Hz。
- 入力・停止・再開19条件PASS。Joy停止後のlinear.x / linear.y / angular.zが0。
- CycloneDDS・Fast DDSのSIGINT終了: 両ノードが正常終了、Python例外なし、起動した子PIDの残存なし。
- 仮想ディスプレイの全画面PNGでGUIと日本語表示を確認。原本とリポジトリへのコピーのhash一致を確認。

最新の[実行結果](JAZZY-004/qualification/rmw_cyclonedds_cpp/runtime-result.json)、
[終了結果](JAZZY-004/qualification/rmw_cyclonedds_cpp/shutdown-result.json)、
[全テスト](JAZZY-004/qualification/all-tests.log)、
[起動画面](JAZZY-004/qualification/rmw_cyclonedds_cpp/readme-launch-display.png)を参照してください。

## 検証条件と未確認項目

検証条件はWSL Ubuntu-24.04-50GB、ROS_DOMAIN_ID=100、ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST、
専用名前空間`/virtual_joy_jazzy_check`、Xvfbの1280×960画面です。
状態APIで入力を設定し、マウス・キーボード入力は合成していません。
合格値は開始時のCONTRACTに固定したCodex側の検証条件であり、ROSの公式条件とは呼びません。

Fast DDSは[最新run](JAZZY-004/qualification/rmw_fastrtps_cpp/runtime-result.json)で15秒の通信タイムアウトです。
[以前の診断run](diagnostics/fastdds-8513fc7/launch-messages.json)では受信成功もあり、原因は未確認です。
確認済みの構成としてREADMEではCycloneDDSを指定しています。
ユーザーのデスクトップ/WSLg画面での手動操作、実機への接続・走行、異なるRMW間通信、新規の別環境での導入は未確認です。

各runにはcommit、実行PID/cwd/引数、実際のRMW/domain、module/launch/設定のSHA-256を保存しています。
検証記録全体のファイルhashはSHA256SUMSを参照してください。
