"""Render the saved CAD model, then encode its turntable and exploded demo.

Run with host Python: python3 hardware/enclosure/animate.py
FreeCAD and FFmpeg must be installed. The native master stays read-only.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT, FPS = 1600, 1200, 24
TURN_SECONDS, EXPLODE_SECONDS, ELECTRONICS_SECONDS = 12, 16, 6
TOTAL_SECONDS = TURN_SECONDS + EXPLODE_SECONDS + ELECTRONICS_SECONDS

# Separate each optical layer along the front axis. Fan out the electronics
# beside the stack. These are illustration positions, not service clearances.
BOARD_POSITIONS = {
    'SparklePCBWithHoles': (-225, -10, -15),
    'blackpillPCB': (-170, -10, -15),
    'gpsPCB': (-225, -65, -15),
    'imuPCB': (-170, -65, -15),
    'radioPCB': (-225, -115, -15),
    'sensePCB': (-170, -115, -15),
    'powerPCB': (-225, -165, -15),
    'BatteryEnvelope0': (-205, 80, -15),
}
BOARD_LABELS = {
    'SparklePCBWithHoles': 'Sparkle Motion',
    'blackpillPCB': 'BlackPill',
    'gpsPCB': 'GPS',
    'imuPCB': 'LSM9DS1 IMU',
    'radioPCB': 'LoRa radio',
    'sensePCB': 'Battery divider',
    'powerPCB': '5 V boost',
    'BatteryEnvelope0': 'Protected 1S LiPo',
}
LAYER_LABELS = {
    'FrontBezel': 'Black acrylic front border',
    'CircleBezel': 'Circle snap rim',
    'FrontAcrylic': 'Central acrylic diffuser',
    'WoodMask': 'Fibonacci wood mask',
    'FrontMirror': 'Two-way mirror annulus',
    'CellBaffle': 'Light-isolation baffle',
    'InnerDiffuser': 'Inner acrylic sleeve',
    'HaloDiffuser': 'Halo acrylic sleeve',
    'HaloLEDs': 'Halo and inward LED strips',
    'CirclePCB': 'Fibonacci256 PCB and LEDs',
    'RearMirror': 'Rear mirror annulus',
    'EdgeDiffuserSeam': 'Outer acrylic sleeve',
    'OpticalDeckQ1': 'Optical deck quarters',
    'BarrelFrameQ1': 'Barrel and outside LED strip',
    'BatteryEnvelope0': 'LiPo and separated boards',
    'RearPlateQ1': 'Ribbed PETG rear quarters',
    'NecklaceLink1': 'Replaceable necklace mounts',
    'VentGuard0': 'Vents, covers and seam straps',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def explosion_offset(name, centre):
    if name in BOARD_POSITIONS:
        return tuple(t - c for t, c in zip(BOARD_POSITIONS[name], centre))
    if name.startswith('RearPlateQ'):
        return (math.copysign(10, centre[0]), math.copysign(10, centre[1]), -90)
    if name.startswith('BarrelFrameQ'):
        return (math.copysign(14, centre[0]), math.copysign(14, centre[1]), 0)
    if name.startswith('OpticalDeckQ'):
        return (math.copysign(14, centre[0]), math.copysign(14, centre[1]), 45)
    if name.startswith('NecklaceLink'):
        return (math.copysign(35, centre[0]), 0, -115)
    if name.startswith('VentGuard'):
        return (0, 0, -150)
    if name.startswith('VentMembrane'):
        return (0, 0, -125)
    if name.startswith('ControlMembrane') or name.startswith('RearButton'):
        return (0, -35, -115)
    if name.startswith('HaloDiffuserPad'):
        return (0, 0, 160)
    if name.startswith('InnerDiffuserPad'):
        return (0, 0, 200)
    layers = {
        'ServiceCover': -160, 'HatchGasket': -135,
        'ExternalPowerBlank': -125, 'SeamStraps': -105,
        'OuterStripSeam': 15, 'OuterLEDs': 15,
        'EdgeDiffuserSeam': 60,
        'RearMirror': 95,
        'CirclePCB': 120, 'CircleLEDs': 120,
        'HaloStripSeam': 145, 'HaloLEDs': 145,
        'InnerStripSeam': 145, 'InnerLEDs': 145,
        'HaloDiffuser': 175, 'InnerDiffuser': 215,
        'CellBaffle': 245, 'WoodMask': 295,
        'FrontMirror': 275, 'FrontAcrylic': 335,
        'FrontBezel': 375, 'CircleBezel': 375,
    }
    if name not in layers:
        raise ValueError('Assign an exploded position to native part: ' + name)
    return (0, 0, layers[name])


def render(frames, output, preview=False):
    import FreeCAD as App
    import FreeCADGui as Gui
    from pivy import coin  # Loads the native camera wrappers.
    from PySide import QtCore, QtGui

    master = HERE / 'smart-compass.FCStd'
    original_hash = digest(master)
    source = App.openDocument(str(master))
    scene = App.newDocument('AmuletAnimation')
    items = []
    try:
        for group in (source.Manufactured, source.Electronics, source.Optics):
            for part in group.Group:
                if not part.Visibility:
                    continue
                obj = scene.addObject('Part::Feature', part.Name)
                obj.Label = part.Label
                obj.Shape = part.Shape.copy()
                obj.ViewObject.ShapeAppearance = part.ViewObject.ShapeAppearance
                obj.ViewObject.LineColor = part.ViewObject.LineColor
                obj.ViewObject.DisplayMode = part.ViewObject.DisplayMode
                obj.ViewObject.Transparency = part.ViewObject.Transparency
                centre = obj.Shape.BoundBox.Center
                items.append((obj, App.Placement(obj.Placement), centre,
                              App.Vector(*explosion_offset(part.Name, tuple(centre)))))
        scene.recompute()
        assert len(items) == len({o.Name for o, *_ in items})
        for name in ('HaloDiffuser', 'InnerDiffuser', 'EdgeDiffuserSeam'):
            assert scene.getObject(name).ViewObject.Transparency == 60
        App.closeDocument(source.Name)
        source = None
        Gui.activeDocument().activeView().setAnimationEnabled(False)
        view = Gui.activeDocument().activeView()
        view.setCameraType('Orthographic')
        camera = view.getCameraNode()
        assert isinstance(camera, coin.SoOrthographicCamera)
        base = App.Rotation(App.Vector(1, 0, 0), -12)
        diagram = App.Rotation(App.Vector(0, 0, 1), 25).multiply(
            App.Rotation(App.Vector(1, 0, 0), 65))

        def pose(rotation, centre, height):
            view.setCameraOrientation(rotation)
            eye = centre + rotation.multVec(App.Vector(0, 0, 1200))
            camera.position.setValue(*tuple(eye))
            camera.focalDistance.setValue(1200)
            camera.nearDistance.setValue(1)
            camera.farDistance.setValue(3000)
            camera.height.setValue(height)

        def move(amount):
            for obj, original, _, delta in items:
                pl = App.Placement(original)
                pl.Base += delta * amount
                obj.Placement = pl
                obj.Visibility = True

        def electronic_layout():
            for obj, original, _, _ in items:
                obj.Visibility = obj.Name in BOARD_POSITIONS
                if obj.Visibility:
                    # A separate inspection spread retains the native scale.
                    index = list(BOARD_POSITIONS).index(obj.Name)
                    target = App.Vector((-95, 15)[index % 2], 100 - 65 * (index // 2), 0)
                    pl = App.Placement(original)
                    pl.Base += target - obj.Shape.BoundBox.Center
                    obj.Placement = pl

        def frame(path, title, subtitle, labels=False, layers=False):
            Gui.updateGui()
            view.saveImage(str(path), WIDTH, HEIGHT, 'White')
            picture = QtGui.QImage(str(path))
            assert not picture.isNull()
            painter = QtGui.QPainter(picture)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.fillRect(0, 0, WIDTH, 112, QtGui.QColor('white'))
            painter.fillRect(0, HEIGHT - 55, WIDTH, 55, QtGui.QColor('white'))
            painter.setPen(QtGui.QColor('#14232e'))
            font = QtGui.QFont('Helvetica')
            font.setPixelSize(37)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(46, 52, title)
            font.setPixelSize(23)
            font.setBold(False)
            painter.setFont(font)
            painter.drawText(46, 91, subtitle)
            font.setPixelSize(19)
            painter.setFont(font)
            painter.drawText(46, HEIGHT - 21,
                             'NATIVE CAD  |  Provisional fit  |  Materials and light transmission are not simulated')
            inverse = view.getCameraOrientation().inverted()
            eye = App.Vector(*tuple(camera.position.getValue()))

            def project(point):
                local = inverse.multVec(point - eye)
                return (WIDTH / 2 + local.x * HEIGHT / camera.height.getValue(),
                        HEIGHT / 2 - local.y * HEIGHT / camera.height.getValue())

            if labels:
                for obj, *_ in items:
                    if not obj.Visibility:
                        continue
                    box = obj.Shape.BoundBox
                    x, _ = project(box.Center)
                    bottom = max(project(App.Vector(a, b, c))[1]
                                 for a in (box.XMin, box.XMax)
                                 for b in (box.YMin, box.YMax)
                                 for c in (box.ZMin, box.ZMax))
                    label = BOARD_LABELS[obj.Name]
                    text_width = painter.fontMetrics().horizontalAdvance(label)
                    painter.fillRect(int(x - text_width / 2 - 8), int(bottom + 12),
                                     text_width + 16, 28, QtGui.QColor('white'))
                    painter.setPen(QtGui.QColor('#14232e'))
                    painter.drawText(int(x - text_width / 2), int(bottom + 34), label)
            if layers:
                anchors = []
                for name, label in LAYER_LABELS.items():
                    box = scene.getObject(name).Shape.BoundBox
                    point = project(App.Vector(box.XMax, box.Center.y, box.Center.z))
                    anchors.append((point, label))
                anchors.sort(key=lambda item: item[0][1])
                for index, ((x, y), label) in enumerate(anchors):
                    baseline = 158 + index * 52
                    painter.setPen(QtGui.QColor('#758895'))
                    painter.drawLine(int(x), int(y), 1148, baseline - 7)
                    painter.fillRect(1152, baseline - 26, 440, 36, QtGui.QColor('white'))
                    painter.setPen(QtGui.QColor('#14232e'))
                    painter.drawText(1160, baseline, label)
            painter.end()
            assert picture.save(str(path))

        def turn(t, path):
            move(0)
            pose(App.Rotation(App.Vector(0, 1, 0), t * 360).multiply(base),
                 App.Vector(0, 0, 20), 345)
            frame(path, 'SMART COMPASS / AMULET',
                  'Full rotation  |  Fibonacci256 + halo + inner ring + outer ring')

        def exploded(t, path):
            if t < .25:
                u = t * 4
                amount = u * u * (3 - 2 * u)
                angle = 0
            elif t <= .3125:
                amount, angle = 1, 0
            elif t <= .6875:
                amount, angle = 1, (t - .3125) * 960
            elif t <= .75:
                amount, angle = 1, 360
            else:
                u = (1 - t) * 4
                amount, angle = u * u * (3 - 2 * u), 360
            move(amount)
            pose(App.Rotation(App.Vector(0, 0, 1), angle).multiply(diagram),
                 App.Vector(-40 * amount, -15 * amount, 20 + 95 * amount),
                 345 + 520 * amount)
            frame(path, 'EXPLODED ASSEMBLY',
                  'Optical layers, three acrylic sleeves, LED strips, frames, rear, battery and boards',
                  layers=amount == 1 and angle in (0, 360))

        def electronics(t, path):
            move(0)
            electronic_layout()
            pose(App.Rotation(App.Vector(0, 1, 0), 14 * math.sin(t * math.tau)),
                 App.Vector(-40, 3, 0), 345)
            frame(path, 'ELECTRONICS AND BATTERY',
                  'Native board footprints and pack envelope  |  Components and wiring remain fit references',
                  labels=True)

        frames.mkdir(parents=True, exist_ok=True)
        output.mkdir(parents=True, exist_ok=True)
        turn(.10, output / 'turntable-poster.png')
        exploded(.25, output / 'exploded-overview.png')
        electronics(0, output / 'electronics-overview.png')
        if not preview:
            index = 0
            for name, seconds, draw in (
                    ('rotation', TURN_SECONDS, turn),
                    ('exploded', EXPLODE_SECONDS, exploded),
                    ('electronics', ELECTRONICS_SECONDS, electronics)):
                count = FPS * seconds
                for i in range(count):
                    draw(i / (count - 1), frames / f'frame-{index:05d}.png')
                    index += 1
                    if i % FPS == 0:
                        print(f'{name}: {i // FPS + 1}/{seconds} s rendered', flush=True)
            assert index == FPS * TOTAL_SECONDS
        assert digest(master) == original_hash, 'Animation changed the native master'
        (frames / 'render-complete.json').write_text(json.dumps({
            'source_sha256': original_hash, 'objects': len(items),
            'frames': 0 if preview else FPS * TOTAL_SECONDS,
            'width': WIDTH, 'height': HEIGHT, 'fps': FPS,
        }, indent=2) + '\n')
        print('CAD ANIMATION RENDER PASS; native master unchanged', flush=True)
    finally:
        App.closeDocument(scene.Name)
        if source is not None:
            App.closeDocument(source.Name)


def encode(frames, output, ffmpeg, ffprobe):
    record = json.loads((frames / 'render-complete.json').read_text())
    assert record['frames'] == FPS * TOTAL_SECONDS
    assert record['source_sha256'] == digest(HERE / 'smart-compass.FCStd')
    files = sorted(frames.glob('frame-*.png'))
    assert len(files) == record['frames']
    assert files[-1].name == f'frame-{record["frames"] - 1:05d}.png'

    def input_args(start, seconds):
        return [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
                '-framerate', str(FPS), '-start_number', str(start),
                '-t', str(seconds), '-i', str(frames / 'frame-%05d.png')]

    video = output / 'amulet-demo.pending.mp4'
    subprocess.run(input_args(0, TOTAL_SECONDS) + [
        '-c:v', 'libx264', '-crf', '19', '-preset', 'medium',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', str(video)], check=True)
    video.replace(output / 'amulet-demo.mp4')
    palette = ('fps=12,scale=800:-1:flags=lanczos,split[a][b];'
               '[a]palettegen=max_colors=128:stats_mode=diff[p];'
               '[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle')
    for name, start, seconds in (
            ('turntable', 0, TURN_SECONDS),
            ('exploded', FPS * TURN_SECONDS, EXPLODE_SECONDS)):
        gif = output / (name + '.pending.gif')
        subprocess.run(input_args(start, seconds) + [
            '-filter_complex', palette, '-loop', '0', str(gif)], check=True)
        gif.replace(output / (name + '.gif'))
    for name, seconds, count, width, height in (
            ('amulet-demo.mp4', TOTAL_SECONDS, FPS * TOTAL_SECONDS, WIDTH, HEIGHT),
            ('turntable.gif', TURN_SECONDS, 12 * TURN_SECONDS, 800, 600),
            ('exploded.gif', EXPLODE_SECONDS, 12 * EXPLODE_SECONDS, 800, 600)):
        path = output / name
        data = json.loads(subprocess.check_output([
            ffprobe, '-v', 'error', '-count_frames', '-show_streams',
            '-show_format', '-of', 'json', str(path)], text=True))
        stream = data['streams'][0]
        assert int(stream['nb_read_frames']) == count, name + ': wrong frame count'
        assert (stream['width'], stream['height']) == (width, height)
        assert abs(float(data['format']['duration']) - seconds) < .12
        subprocess.run([ffmpeg, '-v', 'error', '-i', str(path), '-f', 'null', '-'], check=True)
        print(f'MEDIA CHECK PASS: {name}, {seconds} s, {count} frames, {path.stat().st_size / 1e6:.1f} MB', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='Render only three inspection posters')
    parser.add_argument('--output', type=Path, default=HERE / 'exports')
    args = parser.parse_args()
    freecad = shutil.which('freecad') or '/Applications/FreeCAD.app/Contents/Resources/bin/freecad'
    if not Path(freecad).is_file():
        raise SystemExit('Install FreeCAD with brew install --cask freecad')
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not args.preview and not (ffmpeg and ffprobe):
        raise SystemExit('Install FFmpeg with brew install ffmpeg')
    output = args.output.resolve()
    with tempfile.TemporaryDirectory(prefix='smart-compass-animation-') as directory:
        frames = Path(directory)
        env = dict(os.environ, SC_CAD_DIR=str(HERE), SC_DEMO_FRAMES=str(frames),
                   SC_DEMO_OUTPUT=str(output), SC_DEMO_PREVIEW=str(int(args.preview)))
        subprocess.run([freecad, str(HERE / 'Animate.FCMacro')], env=env, check=True)
        assert (frames / 'render-complete.json').exists(), 'Native render failed; inspect FreeCAD output'
        if not args.preview:
            encode(frames, output, ffmpeg, ffprobe)


if __name__ == '__main__':
    main()
