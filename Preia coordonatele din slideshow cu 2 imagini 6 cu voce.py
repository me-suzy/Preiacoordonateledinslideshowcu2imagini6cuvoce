import os
import cv2
import numpy as np
import re
from gtts import gTTS
import time
import threading
import tkinter as tk
from PIL import Image, ImageTk
import pygame
import sys

# Coordonatele fixe pentru detectare
COORD_STÂNGA = (127, 1323)
COORD_DREAPTA = (285, 1316)

class SlideshowAutomatizat:
    def __init__(self, images_paths):
        self.images_paths = images_paths
        self.current_image = 0
        self.running = True
        self.auto_play = True

        # Google Vision credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"d:\77\bebe-1084-fcc3d60b38d6.json"

        # Crează fereastra
        self.root = tk.Tk()
        self.root.title("Slideshow Automat cu Numere")
        self.root.configure(bg='black')
        self.root.state('zoomed')

        # Imagine
        self.image_label = tk.Label(self.root, bg='black')
        self.image_label.pack(expand=True, fill='both')

        # Status bar
        self.status_frame = tk.Frame(self.root, bg='gray20', height=50)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        self.status_label = tk.Label(self.status_frame, text="Pregătire...",
                                   bg='gray20', fg='white', font=('Arial', 12))
        self.status_label.pack(pady=15)

        # Controale
        self.root.bind('<KeyPress>', self.key_press)
        self.root.focus_set()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def detect_number_at_coordinate(self, image_path, x, y, nume_pozitie):
        """Detectează numărul la o coordonată"""
        try:
            from google.cloud import vision
            image = cv2.imread(image_path)
            if image is None:
                return None
            margin = 50
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(image.shape[1], x + margin)
            y2 = min(image.shape[0], y + margin)
            region = image[y1:y2, x1:x2]
            scale = 4
            enlarged = cv2.resize(region, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            temp_file = "temp_region.png"
            cv2.imwrite(temp_file, enlarged)
            client = vision.ImageAnnotatorClient()
            with open(temp_file, 'rb') as f:
                content = f.read()
                vision_image = vision.Image(content=content)
            response = client.text_detection(image=vision_image)
            try:
                os.remove(temp_file)
            except:
                pass
            if response.text_annotations:
                text = response.text_annotations[0].description.strip()
                numbers = re.findall(r'\d+', text)
                valid_numbers = [int(num) for num in numbers if num.isdigit() and 10 <= int(num) <= 200]
                if valid_numbers:
                    return max(valid_numbers)
            return None
        except Exception as e:
            print(f"Eroare la detectare: {e}")
            return None

    def detect_numbers_from_image(self, image_path):
        """Detectează ambele numere dintr-o imagine"""
        numar_stanga = self.detect_number_at_coordinate(image_path,
                                                       COORD_STÂNGA[0],
                                                       COORD_STÂNGA[1],
                                                       "stânga")
        numar_dreapta = self.detect_number_at_coordinate(image_path,
                                                        COORD_DREAPTA[0],
                                                        COORD_DREAPTA[1],
                                                        "dreapta")
        return numar_stanga, numar_dreapta

    def announce_numbers(self, stanga, dreapta, image_name):
        """Anunță numerele cu voce"""
        if stanga and dreapta:
            message = f"În {image_name}, numărul din stânga este {stanga}, numărul din dreapta este {dreapta}"
        elif stanga:
            message = f"În {image_name}, doar numărul din stânga este {stanga}"
        elif dreapta:
            message = f"În {image_name}, doar numărul din dreapta este {dreapta}"
        else:
            message = f"În {image_name}, nu am detectat numere valide"

        try:
            tts = gTTS(text=message, lang='ro')
            audio_file = "announcement.mp3"
            tts.save(audio_file)
            pygame.mixer.init()
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            os.remove(audio_file)
        except Exception as e:
            print(f"Eroare la anunțul vocal: {e}")

    def show_image(self, image_path):
        """Afișează o imagine în fereastră"""
        try:
            pil_image = Image.open(image_path)
            self.root.update_idletasks() # Asigură că dimensiunile ferestrei sunt actuale
            width = self.root.winfo_width() - 100
            height = self.root.winfo_height() - 150
            if width > 0 and height > 0:
                pil_image.thumbnail((width, height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(pil_image)
            self.image_label.config(image=photo)
            self.image_label.image = photo
            filename = os.path.basename(image_path)
            self.root.title(f"Slideshow - {filename}")
        except Exception as e:
            print(f"Eroare la afișarea imaginii: {e}")

    def slideshow_loop(self):
        """Bucla principală a slideshow-ului"""
        while self.running:
            if self.auto_play:
                image_path = self.images_paths[self.current_image]
                filename = os.path.basename(image_path)

                print(f"\n=== PROCESEZ IMAGINEA {self.current_image + 1}: {filename} ===")
                self.status_label.config(text=f"Afișez: {filename}")
                self.show_image(image_path)

                # Așteaptă 2 secunde pentru a permite vizualizarea imaginii
                time.sleep(2)

                self.status_label.config(text="Detectez numere...")
                stanga, dreapta = self.detect_numbers_from_image(image_path)

                self.status_label.config(text="Anunț vocal...")
                image_name = filename.replace('.png', '').replace('Google Maps Speed Road Car ', 'imaginea ')
                self.announce_numbers(stanga, dreapta, image_name)

                # Trece la următoarea imagine
                self.current_image = (self.current_image + 1) % len(self.images_paths)
            else:
                time.sleep(0.5)

    def key_press(self, event):
        """Gestionează apăsările de taste"""
        key = event.keysym.lower()
        if key == 'escape':
            self.close_app()
        elif key == 'space':
            self.auto_play = not self.auto_play
            if self.auto_play:
                print("Slideshow pornit")
                threading.Thread(target=self.slideshow_loop, daemon=True).start()
            else:
                print("Slideshow oprit")

    def close_app(self):
        """Închide aplicația"""
        print("Închid slideshow-ul...")
        self.running = False
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def start(self):
        """Pornește slideshow-ul"""
        print("=== SLIDESHOW AUTOMAT CU DETECTARE NUMERE ===")
        print("Controale:")
        print("  SPAȚIU = pornește/oprește slideshow-ul")
        print("  ESC = ieșire")
        print("\nSlideshow-ul pornește automat în 2 secunde...")

        self.show_image(self.images_paths[0])
        self.status_label.config(text="Gata de pornire - apasă Spațiu")

        def start_auto():
            time.sleep(2)
            if self.running:
                self.auto_play = True
                threading.Thread(target=self.slideshow_loop, daemon=True).start()

        threading.Thread(target=start_auto, daemon=True).start()
        self.root.mainloop()

def main():
    """Funcția principală"""
    images = [
        r"d:\77\Google Maps Speed Road Car 1.png",
        r"d:\77\Google Maps Speed Road Car 2.png"
    ]
    existing_images = [img for img in images if os.path.exists(img)]
    if not existing_images:
        print("✗ Nu s-a găsit nicio imagine!")
        return

    slideshow = SlideshowAutomatizat(existing_images)
    slideshow.start()

if __name__ == "__main__":
    main()