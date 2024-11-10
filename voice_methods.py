import assemblyai as aai
import os
import dotenv

dotenv.load_dotenv()


def transcribe_audio(file_url: str = None, file_path: str = None):
    # Replace with your API token
    aai.settings.api_key = os.getenv("AAI_API_KEY")

    # URL of the file to transcribe
    FILE_URL = "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"

    # You can also transcribe a local file by passing in a file path
    # FILE_URL = './path/to/file.mp3'

    config = aai.TranscriptionConfig(speaker_labels=True)

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(
        file_url if file_url else file_path,
        config=config
    )

    print(transcript)

    print(transcript.utterances)

    for utterance in transcript.utterances or []:
        print(f"Speaker {utterance.speaker}: {utterance.text}")

    return transcript.utterances



if __name__ == "__main__":

    import streamlit as st

    FILE_URL = "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"

    audio_value = st.audio_input("Record a voice message")

    if audio_value:
        st.audio(audio_value)

        # save the audio to a file
        with open("audio.mp3", "wb") as f:
            f.write(audio_value.getvalue())

        # transcribe the audio
        transcript = transcribe_audio(file_path="audio.mp3")

        # write a streamlit chat from the transcript
        for utterance in transcript or []:
            st.chat_message(utterance.speaker).markdown(utterance.text)

    if FILE_URL:
        transcript = transcribe_audio(file_url=FILE_URL)

        # write a streamlit chat from the transcript
        for utterance in transcript or []:
            st.chat_message(utterance.speaker).markdown(utterance.text)


