"""Check LED motion independently of the camera in the matched rainbow clips."""

import subprocess


def verify_rainbow_motion(movie):
    """Compare central cells at equal camera poses and different rainbow phases."""
    frames = []
    for seconds in (2, 14, 4, 12):
        frames.append(
            subprocess.check_output(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-ss",
                    str(seconds),
                    "-i",
                    str(movie),
                    "-frames:v",
                    "1",
                    "-vf",
                    "crop=64:64",
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "rgb24",
                    "-",
                ]
            )
        )
    if any(len(frame) != 64 * 64 * 3 for frame in frames):
        raise RuntimeError("Incomplete rainbow motion samples: " + str(movie))
    # Times 2/14 have the same view and opposite hues. Times 4/12 also have
    # the same view, but identical hues, so measure the codec/render noise.
    change = sum(abs(a - b) for a, b in zip(frames[0], frames[1])) / (
        len(frames[0]) * 255
    )
    repeat_error = sum(abs(a - b) for a, b in zip(frames[2], frames[3])) / (
        len(frames[2]) * 255
    )
    if change <= max(0.01, 3 * repeat_error):
        raise RuntimeError(
            "Rainbow MP4 has no distinct central LED colour motion: " + str(movie)
        )
    print(
        f"MOVIE MOTION PASS: {movie.name}; central RGB change {change:.5f}; repeat noise {repeat_error:.5f}",
        flush=True,
    )
