import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import os
import random
from time import time 
import json


class ImageFrame:
    frame_sizes = {
        0: (21, 29.7),  # L
        1: (15, 20),    # M
        2: (13, 18)     # S
    }

    def __init__(self, path, size_index):
        self.path = path
        self.size_index = size_index
        self.frame_size = self.frame_sizes[self.size_index]  # Ensure the frame size is correct
        self.original_frame_size = self.frame_size
        self.image = Image.open(path)
        self.orientation = None
        self.update_orientation()
        self.update_transformed_image()
        self.x = 0
        self.y = 0
        self.width = self.transformed_image.width
        self.height = self.transformed_image.height
        self.tk_id = None

    def get_size_index(self, frame_size):
        """Return the index for a given frame size."""
        for index, size in self.frame_sizes.items():
            if size == frame_size:
                return index
        raise ValueError(f"Frame size {frame_size} not found in frame_sizes.")

    def update_orientation(self):
        img_aspect_ratio = self.image.width / self.image.height
        frame_aspect_ratio = self.frame_size[0] / self.frame_size[1]
        self.orientation = 1 if img_aspect_ratio > frame_aspect_ratio else 0

        if self.orientation == 1 and self.frame_size[0] < self.frame_size[1]:
            self.frame_size = (self.frame_size[1], self.frame_size[0])
        elif self.orientation == 0 and self.frame_size[0] > self.frame_size[1]:
            self.frame_size = (self.frame_size[1], self.frame_size[0])

        self.update_transformed_image()

    def create_transformed_image(self):
        w, h = self.frame_size
        img_aspect_ratio = self.image.width / self.image.height
        frame_aspect_ratio = w / h

        if img_aspect_ratio > frame_aspect_ratio:
            new_width = self.image.width
            new_height = int(self.image.width / frame_aspect_ratio)
        else:
            new_height = self.image.height
            new_width = int(self.image.height * frame_aspect_ratio)
        
        left = (self.image.width - new_width) / 2
        top = (self.image.height - new_height) / 2
        right = (self.image.width + new_width) / 2
        bottom = (self.image.height + new_height) / 2
        cropped_img = self.image.crop((left, top, right, bottom))
        
        resized_img = cropped_img.resize((int(w * 10), int(h * 10)), Image.LANCZOS)
        
        draw = ImageDraw.Draw(resized_img)
        frame_border = 10
        draw.rectangle(
            [0, 0, resized_img.width - 1, resized_img.height - 1],
            outline="black",
            width=frame_border
        )
        return resized_img

    def update_transformed_image(self):
        """Update the image according to the frame size and orientation."""
        self.transformed_image = self.create_transformed_image()
        self.tk_image = ImageTk.PhotoImage(self.transformed_image)

    def get_resized_dimensions(self, img_aspect_ratio, frame_width, frame_height):
        if img_aspect_ratio > (frame_width / frame_height):  # Image is wider
            new_width = self.image.width
            new_height = int(self.image.width / (frame_width / frame_height))
        else:  # Image is taller or square
            new_height = self.image.height
            new_width = int(self.image.height * (frame_width / frame_height))
        
        return new_width, new_height

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def get_position(self):
        return self.x, self.y

    def rotate_frame(self):
        self.size_index = (self.size_index + 1) % len(self.frame_sizes)
        self.frame_size = self.frame_sizes[self.size_index]
        self.update_transformed_image()


class PhotoWallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Wall Gallery")
        self.root.state('zoomed')
        self.root.bind("<Escape>", self.exit_fullscreen)
        
        self.frame_sizes = {'L': (21, 29.7), 'M': (15, 20), 'S': (13, 18)}
        self.selected_frame_size = 'L'  # Initialize the selected frame size
        self.images_on_wall = []
        self.selected_image = None
        self.start_x = self.start_y = 0
        
        # Flag to prevent multiple deletions
        self.deletion_in_progress = time()
        
        # Create a frame for displaying the number of images of each size
        self.side_frame = tk.Frame(root, width=200, bg="lightgray")
        self.side_frame.pack(side="left", fill="y")
        self.size_counts = tk.Label(self.side_frame, text="", bg="lightgray")
        self.size_counts.pack(padx=10, pady=10)
        
        self.update_size_counts()
        
        # Create a frame for buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side="top", fill="x", pady=10)

        # Use grid to center the frame
        self.button_frame.grid_rowconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure((0, 1, 2), weight=1)  # Ensure equal distribution

        # Load Images Button
        self.load_images_button = tk.Button(self.button_frame, text="Load Images", command=self.load_images)
        self.load_images_button.grid(row=0, column=0, padx=5, pady=5)

        # Add buttons for saving and loading the state
        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_state)
        self.save_button.grid(row=0, column=1, padx=5, pady=5)

        self.load_button = tk.Button(self.button_frame, text="Load", command=self.load_state)
        self.load_button.grid(row=0, column=2, padx=5, pady=5)

        
        # Canvas for displaying the wall
        self.wall = tk.Canvas(root, bg="white")
        self.wall.pack(side="right", fill="both", expand=True)
        
        self.wall.bind("<Button-1>", self.start_drag)
        self.wall.bind("<B1-Motion>", self.drag_image)
        self.wall.bind("<ButtonRelease-1>", self.end_drag)
        self.wall.bind("<Button-2>", self.delete_image)
        self.wall.bind("<Button-3>", self.select_image)  # Bind right click to select and toggle size
        
        self.redraw_canvas()

    def exit_fullscreen(self, event=None):
        self.root.attributes('-fullscreen', False)
    
    def load_images(self):
        # folder_path = 'resized/'
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.images_on_wall = []
            self.wall.delete("all")
            
            # Get the width of the wall (canvas)
            max_width = self.wall.winfo_width()
            x_offset = 10  # Start position for the first image
            y_offset = 10  # Top padding
            padding = 20    # Space between images

            for img_file in os.listdir(folder_path):
                if img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(folder_path, img_file)
                    image_frame = ImageFrame(img_path, size_index=2)
                    
                    # Set position for each image
                    image_frame.set_position(x_offset, y_offset)
                    self.images_on_wall.append(image_frame)

                    # Update the x position for the next image
                    x_offset += image_frame.transformed_image.width + padding

                    # If the x position exceeds the canvas width, move to the next row
                    if x_offset > max_width - 1.5*image_frame.transformed_image.width:
                        x_offset = 10
                        y_offset += image_frame.transformed_image.height + padding

            self.redraw_canvas()
            self.update_size_counts()

    
    def save_state(self):
        state = []
        for img in self.images_on_wall:
            state.append({
                'path': img.path,
                'size_index': img.size_index,
                'position': img.get_position()
            })
        with open("wall_state.json", "w") as f:
            json.dump(state, f)
        print("State saved to wall_state.json")

    def load_state(self):
        self.images_on_wall = []
        self.wall.delete("all")
        if os.path.exists("wall_state.json"):
            with open("wall_state.json", "r") as f:
                state = json.load(f)
            for img_data in state:
                img_path = img_data['path']
                size_index = img_data['size_index']
                position = img_data['position']
                image_frame = ImageFrame(img_path, size_index)
                image_frame.set_position(*position)
                self.images_on_wall.append(image_frame)
            self.redraw_canvas()
            self.update_size_counts()
            print("State loaded from wall_state.json")
        else:
            print("No saved state found")
    
    def toggle_size(self, image_frame):
        num_sizes = len(ImageFrame.frame_sizes)
        current_size_index = image_frame.size_index
        next_size_index = (current_size_index + 1) % num_sizes
        
        # Update the image frame size
        image_frame.size_index = next_size_index
        new_frame_size = image_frame.frame_sizes[next_size_index] 
        
        # Set the new frame size and update orientation if needed
        image_frame.frame_size = new_frame_size
        image_frame.update_orientation()
        
        # Ensure the image size is updated based on the new frame size
        image_frame.update_transformed_image()
        image_frame.tk_image = ImageTk.PhotoImage(image_frame.transformed_image)

        # Adjust position to prevent jumping
        image_frame.width = image_frame.transformed_image.width
        image_frame.height = image_frame.transformed_image.height

        # Reposition image to prevent jumping
        x, y = image_frame.get_position()
        image_frame.set_position(x, y)
        self.redraw_canvas()
        self.update_size_counts()
        
    def randomize_position(self, image_frame, positions, max_attempts=100):
        max_width = self.wall.winfo_width()
        max_height = self.wall.winfo_height()
        image_frame.width = image_frame.transformed_image.width
        image_frame.height = image_frame.transformed_image.height

        for _ in range(max_attempts):
            x = random.randint(0, max_width - image_frame.width)
            y = random.randint(0, max_height - image_frame.height)
            
            if not any(self.overlaps(x, y, img.get_position(), image_frame.width, image_frame.height) for img in positions):
                image_frame.set_position(x, y)
                positions.append(image_frame)
                return

        image_frame.set_position(random.randint(0, max_width - image_frame.width), 
                                random.randint(0, max_height - image_frame.height))
        positions.append(image_frame)

    def overlaps(self, x1, y1, pos2, width, height):
        x2, y2 = pos2
        return not (x1 + width < x2 or x1 > x2 + width or y1 + height < y2 or y1 > y2 + height)
    
    def redraw_canvas(self):
        self.wall.delete("all")
        for img in self.images_on_wall:
            img.tk_id = self.wall.create_image(img.x, img.y, anchor="nw", image=img.tk_image)
            self.wall.tag_bind(img.tk_id, "<Button-1>", self.select_image)
            self.wall.tag_bind(img.tk_id, "<Button-2>", self.delete_image)
            self.wall.tag_bind(img.tk_id, "<B1-Motion>", self.drag_image)
    
    def update_size_counts(self):
        size_counts = [0]*len(ImageFrame.frame_sizes)
        size_labels = ['L', 'M', 'S', 'XS']
        for img in self.images_on_wall:
            size_counts[img.size_index] += 1
        counts_text = "\n".join(f"Size {size_labels[n]}: {size_counts[n]}" for n in range(len(size_counts)))
        self.size_counts.config(text=counts_text)
    
    def start_drag(self, event):
        for img in self.images_on_wall:
            x1, y1 = img.get_position()
            x2, y2 = x1 + img.width, y1 + img.height
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.selected_image = img
                self.start_x = event.x
                self.start_y = event.y
                return
    
    def drag_image(self, event):
        if self.selected_image:
            dx = event.x - self.start_x
            dy = event.y - self.start_y
            new_x, new_y = self.selected_image.get_position()
            self.selected_image.set_position(new_x + dx, new_y + dy)
            self.redraw_canvas()
            self.start_x = event.x
            self.start_y = event.y
    
    def end_drag(self, event):
        self.selected_image = None

    def select_image(self, event):
        for img in self.images_on_wall:
            x1, y1 = img.get_position()
            x2, y2 = x1 + img.width, y1 + img.height
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.selected_image = img
                if event.num == 3:  # Right-click to toggle size
                    self.toggle_size(img)
                    self.update_size_counts()
                self.redraw_canvas()
                return
    
    def delete_image(self, event):
        if time() - self.deletion_in_progress < 0.05:  # Prevent multiple deletions
            return
        self.deletion_in_progress = time()
        
        closest_image = None
        min_distance = float('inf')
        
        # Find the closest image to the click position
        for img in self.images_on_wall:
            x1, y1 = img.get_position()
            x2, y2 = x1 + img.width, y1 + img.height
            # Calculate distance from the center of the image to the click position
            center_x = x1 + img.width / 2
            center_y = y1 + img.height / 2
            distance = ((event.x - center_x) ** 2 + (event.y - center_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_image = img
        
        # Remove the closest image
        if closest_image:
            self.images_on_wall.remove(closest_image)
            if closest_image.tk_id is not None:
                self.wall.delete(closest_image.tk_id)  # Remove image from canvas
            self.redraw_canvas()
            self.update_size_counts()
        



if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoWallApp(root)
    root.mainloop()
