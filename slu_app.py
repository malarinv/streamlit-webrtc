import logging
import logging.handlers
import queue

# import urllib.request
from pathlib import Path

# from typing import List, NamedTuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal  # type: ignore

# import av
# import cv2
# import numpy as np
import streamlit as st  # from aiortc.contrib.media import MediaPlayer


from streamlit_webrtc import (
    ClientSettings,
    WebRtcMode,
    webrtc_streamer,
)
from streamlit_webrtc.vad import VADUtterance

HERE = Path(__file__).parent

logger = logging.getLogger(__name__)


WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": False, "audio": True},
)


def main():
    # st.header("WebRTC demo")

    # object_detection_page = "Real time object detection (sendrecv)"
    # video_filters_page = (
    #     "Real time video transform with simple OpenCV filters (sendrecv)"
    # )
    # streaming_page = (
    #     "Consuming media files on server-side and streaming it to browser (recvonly)"
    # )
    # sendonly_page = "WebRTC is sendonly and images are shown via st.image() (sendonly)"
    # loopback_page = "Simple video loopback (sendrecv)"
    slu_page = "Numeric SLU"
    # app_mode = st.sidebar.selectbox(
    #     "Choose the app mode",
    #     [
    #         slu_page,
    #     ],
    # )
    st.header(slu_page)
    app_slu()


def app_slu():
    """ Simple audio slu """
    webrtc_ctx = webrtc_streamer(
        key="audio_slu",
        mode=WebRtcMode.SENDONLY,
        client_settings=WEBRTC_CLIENT_SETTINGS,
        video_transformer_factory=None,  # NoOp
    )
    if webrtc_ctx.audio_receiver:
        from plume.utils.transcribe import triton_transcribe_grpc_gen

        vad = VADUtterance()
        frame_len = st.empty()
        transcriber, audio_prep = triton_transcribe_grpc_gen(
            asr_host="101.53.142.218",
            asr_port=8001,
            asr_model="slu_wav2vec2",
            method="whole",
            sep=" ",
        )

        def frame_gen():
            while True:
                try:
                    frame = webrtc_ctx.audio_receiver.get_frame(timeout=1)
                    yield frame
                except queue.Empty:
                    print("Queue is empty. Stop the loop.")
                    webrtc_ctx.audio_receiver.stop()
                    break

        for voice_frame in vad.stream_utterance(frame_gen()):
            transcript = transcriber(audio_prep(voice_frame))
            frame_len.text(f"Transcript: {transcript}")
            # frame_len.text(
            #     f"received voice frame of duration {voice_frames.duration_seconds}"
            # )
    else:
        st.text("no audio receiver")


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)7s from %(name)s in %(pathname)s:%(lineno)d: "
        "%(message)s",
        force=True,
    )

    logger.setLevel(level=logging.DEBUG)

    st_webrtc_logger = logging.getLogger("streamlit_webrtc")
    st_webrtc_logger.setLevel(logging.INFO)

    fsevents_logger = logging.getLogger("fsevents")
    fsevents_logger.setLevel(logging.WARNING)

    main()
