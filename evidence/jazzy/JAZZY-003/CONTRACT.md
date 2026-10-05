# JAZZY-003: ament_python依存キーの解決失敗

- 対象: Ubuntu 24.04 / ROS 2 Jazzy。
- 観測: rosdepがpackage.xmlのbuildtool_depend=ament_pythonを解決できずexit 2になる。
- 原因仮説: Python build typeの名前をインストール対象の依存キーとして宣言している。
- 原因を示す値: `rosdep check --from-paths <src> --ignore-src --rosdistro jazzy`の出力、Jazzy同梱ros2 pkg createの生成manifestとの比較。
- 変更許可: `package.xml`の該当buildtool_depend行だけ。build_type=ament_pythonは維持する。
- 変更禁止: Python runtime依存、GUI、入力、速度、launch、setup.py。
- 制御環境の合格条件: rosdep checkがexit 0。colcon buildが成功し、両console entrypointとlaunchが導入される。
- 実対象の合格条件: ユーザーの導入環境で同じ依存解決・ビルドを確認。
- 再現ログと生成manifestを先にcommit/pushし、確認後に修正する。

