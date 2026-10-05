# 原因の確認

rosdepの再現ログは`ament_python`キーをUbuntu nobleで解決できないと示しています。
Jazzy同梱の`ros2 pkg create --build-type ament_python`で作ったmanifestには、そのbuildtool_dependがありません。
生成manifestは`reproduction/jazzy-template-package.xml`に保存しました。

package.xmlから解決できないbuildtool_dependを削除します。
Pythonパッケージのbuild_typeとしての`ament_python`と、rclpy/Tk/messages/launchのruntime依存は保持します。
再現と同じrosdep checkのexit 0、およびcolconによる両entrypointの導入で確認します。
