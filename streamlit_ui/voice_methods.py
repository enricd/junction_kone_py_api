import assemblyai as aai
import os
import dotenv

dotenv.load_dotenv()


def transcribe_audio_assemblyai(file_url: str = None, file_path: str = None):
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


def transcribe_audio_openai(file_url: str = None, file_path: str = None):
    pass


def transcribe_audio_google(file_url: str = None, file_path: str = None):
    from google.cloud import speech_v1p1beta1 as speech

    client = speech.SpeechClient()

    speech_file = "resources/commercial_mono.wav"

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=2,
        max_speaker_count=4,
    )

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        language_code="en-US",
        diarization_config=diarization_config,
    )

    print("Waiting for operation to complete...")
    response = client.recognize(config=config, audio=audio)

    # The transcript within each result is separate and sequential per result.
    # However, the words list within an alternative includes all the words
    # from all the results thus far. Thus, to get all the words with speaker
    # tags, you only have to take the words list from the last result:
    result = response.results[-1]

    words_info = result.alternatives[0].words

    # Printing out the output:
    for word_info in words_info:
        print(f"word: '{word_info.word}', speaker_tag: {word_info.speaker_tag}")

    return result



if __name__ == "__main__":

    import streamlit as st

    transcribe_audio = transcribe_audio_assemblyai

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


