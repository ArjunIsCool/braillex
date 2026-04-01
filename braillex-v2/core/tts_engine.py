import threading

try:
    import pyttsx3

    PYTTSX3_OK = True
except ImportError:
    PYTTSX3_OK = False

try:
    from deep_translator import GoogleTranslator

    DEEP_TRANSLATOR_OK = True
except ImportError:
    DEEP_TRANSLATOR_OK = False

try:
    from google_trans_new import google_translator

    TRANSLATOR_OK = True
except ImportError:
    TRANSLATOR_OK = False


class TTSEngine:
    def __init__(self):
        self.enabled = PYTTSX3_OK
        self.rate = 150
        self.volume = 0.9
        self.language = "en"
        self._translator = None
        self._translator_type = None
        self.supported_languages = set()
        self._fallback_language = "en"
        self._speech_lock = threading.Lock()

        if PYTTSX3_OK:
            try:
                engine = pyttsx3.init()
                self._detect_supported_languages_with_engine(engine)
                engine = None
            except Exception as e:
                self.enabled = False
                print(f"TTS initialization error: {e}")

        if not self.supported_languages:
            self.supported_languages = {"en"}

    def _detect_supported_languages_with_engine(self, engine):
        if not engine:
            return

        potential_langs = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "hi": "Hindi",
            "ar": "Arabic",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ta": "Tamil",
        }

        self.supported_languages = {"en"}

        translator = None
        translator_type = None

        if DEEP_TRANSLATOR_OK:
            try:
                translator = GoogleTranslator(source="en")
                translator_type = "deep_translator"
            except Exception:
                translator = None

        if translator is None and TRANSLATOR_OK:
            try:
                translator = google_translator()
                translator_type = "google_trans_new"
            except Exception:
                translator = None

        if translator:
            for lang_code, lang_name in potential_langs.items():
                if lang_code != "en":
                    try:
                        if translator_type == "deep_translator":
                            result = translator.translate(
                                "hello", target_language=lang_code
                            )
                        else:
                            result = translator.translate("hello", lang_tgt=lang_code)
                        if result:
                            self.supported_languages.add(lang_code)
                    except Exception:
                        pass

    def get_supported_languages(self):
        return list(self.supported_languages)

    def is_language_supported(self, lang_code):
        return lang_code in self.supported_languages

    def set_voice_rate(self, rate):
        self.rate = max(50, min(300, rate))

    def set_language(self, lang_code):
        if not self.is_language_supported(lang_code):
            self.language = self._fallback_language
            return False

        self.language = lang_code

        if lang_code != "en":
            try:
                if DEEP_TRANSLATOR_OK:
                    try:
                        self._translator = GoogleTranslator(
                            source="en", target=lang_code
                        )
                        self._translator_type = "deep_translator"
                        return True
                    except Exception:
                        if TRANSLATOR_OK:
                            try:
                                self._translator = google_translator()
                                self._translator_type = "google_trans_new"
                                return True
                            except Exception:
                                self.language = self._fallback_language
                                return False
                        else:
                            raise Exception("No translation provider available")
                elif TRANSLATOR_OK:
                    self._translator = google_translator()
                    self._translator_type = "google_trans_new"
                    return True
                else:
                    raise Exception("No translation provider available")
            except Exception:
                self.language = self._fallback_language
                return False
        else:
            self._translator = None
            self._translator_type = None
            return True

    def translate_text(self, text):
        if self.language == "en":
            return text

        if not self.is_language_supported(self.language):
            self.language = self._fallback_language
            return text

        try:
            if not self._translator:
                return text

            if self._translator_type == "deep_translator":
                result = self._translator.translate(text)
                return result if result else text
            else:
                result = self._translator.translate(text, lang_tgt=self.language)
                return result if result else text
        except Exception:
            self.language = self._fallback_language
        return text

    def speak(self, text):
        if not self.enabled:
            return

        with self._speech_lock:
            try:
                if not self.is_language_supported(self.language):
                    self.language = self._fallback_language

                text_to_speak = self.translate_text(text)

                engine = pyttsx3.init()
                engine.setProperty("rate", self.rate)
                engine.setProperty("volume", self.volume)
                engine.say(text_to_speak)
                engine.runAndWait()
                del engine
            except Exception:
                try:
                    if self.language != "en":
                        self.language = "en"
                        engine = pyttsx3.init()
                        engine.setProperty("rate", self.rate)
                        engine.setProperty("volume", self.volume)
                        engine.say(text)
                        engine.runAndWait()
                        del engine
                except Exception:
                    pass

    def speak_letter(self, letter):
        if not self.enabled:
            return
        self.speak(f"{letter}.")

    def speak_async(self, text):
        if not self.enabled:
            return

        def _do_speak():
            self.speak(text)

        threading.Thread(target=_do_speak, daemon=True).start()
