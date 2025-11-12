import os
import numpy as np
from tensorflow.keras.preprocessing import image_dataset_from_directory
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

# ---------------- CONFIG ----------------
DATA_DIR = "fer_data"
IMG_SIZE = 48
BATCH_SIZE = 32
EPOCHS = 25
# ----------------------------------------

# Check if folders exist
train_dir = os.path.join(DATA_DIR, "train")
test_dir = os.path.join(DATA_DIR, "test")

if not os.path.isdir(train_dir) or not os.path.isdir(test_dir):
    print("❌ Dataset not found!")
    print("Please make sure you have this structure:")
    print("fer_data/train/<emotion folders>")
    print("fer_data/test/<emotion folders>")
    exit(1)

print("✅ Loading FER-2013 dataset from image folders...")

# Load train and test datasets
train_dataset = image_dataset_from_directory(
    train_dir,
    image_size=(IMG_SIZE, IMG_SIZE),
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    shuffle=True,
)

test_dataset = image_dataset_from_directory(
    test_dir,
    image_size=(IMG_SIZE, IMG_SIZE),
    color_mode="grayscale",
    batch_size=BATCH_SIZE,
    shuffle=False,
)

# Normalize pixel values
train_dataset = train_dataset.map(lambda x, y: (x / 255.0, y))
test_dataset = test_dataset.map(lambda x, y: (x / 255.0, y))

# ---------------- MODEL BUILDING ----------------
print("🧠 Building CNN model for emotion recognition...")

model = Sequential([
    Conv2D(64, (3, 3), activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 1)),
    MaxPooling2D(2, 2),
    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D(2, 2),
    Dropout(0.25),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(7, activation='softmax')  # 7 emotion categories
])

model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

model.summary()

# ---------------- TRAINING ----------------
print("🚀 Starting training...")

checkpoint_path = os.path.join(os.path.dirname(__file__), "emotion_model_best.h5")
checkpoint = ModelCheckpoint(
    checkpoint_path, monitor='val_accuracy', save_best_only=True, verbose=1
)
early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

history = model.fit(
    train_dataset,
    validation_data=test_dataset,
    epochs=EPOCHS,
    callbacks=[checkpoint, early_stop],
    verbose=1
)

# ---------------- SAVE FINAL MODEL ----------------
model_path = os.path.join(os.path.dirname(__file__), "emotion_model.h5")
model.save(model_path)

print("✅ Training complete!")
print(f"Model saved as: {model_path}")
print("You can now load this model in your Flask app for webcam detection.")
