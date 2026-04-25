"""Deep learning model training with PyTorch LSTM."""
import os
import json
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import structlog

from app.config import get_settings
settings = get_settings()


logger = structlog.get_logger()


class PriceLSTM(nn.Module):
    """LSTM model for price direction prediction."""
    
    def __init__(self, input_size: int, hidden: int = 64, layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.hidden = hidden
        self.layers = layers
        self.input_size = input_size
        
        self.lstm = nn.LSTM(
            input_size,
            hidden,
            layers,
            batch_first=True,
            dropout=dropout if layers > 1 else 0
        )
        self.fc = nn.Linear(hidden, 1)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])  # Take last timestep
        out = self.fc(out)
        return torch.sigmoid(out)


class PriceDataset(Dataset):
    """Dataset for price sequences."""
    
    def __init__(self, X: np.ndarray, y: np.ndarray, seq_length: int = 30):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y).unsqueeze(1) if len(y.shape) == 1 else torch.FloatTensor(y)
        self.seq_length = seq_length
        
    def __len__(self):
        return len(self.X) - self.seq_length + 1
    
    def __getitem__(self, idx):
        return (
            self.X[idx:idx + self.seq_length],
            self.y[idx + self.seq_length - 1]
        )


def create_sequences(X: np.ndarray, y: np.ndarray, seq_length: int = 30) -> Tuple[np.ndarray, np.ndarray]:
    """Create sequences for LSTM training."""
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_length + 1):
        X_seq.append(X[i:i + seq_length])
        y_seq.append(y[i + seq_length - 1])
    return np.array(X_seq), np.array(y_seq)


def train_and_save(
    symbol: str,
    X: np.ndarray,
    y: np.ndarray,
    cache_dir: Optional[str] = None,
    seq_length: int = 30,
    batch_size: int = 32,
    epochs: int = 50,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-5,
    patience: int = 7,
    hidden: int = 64,
    layers: int = 2,
    dropout: float = 0.2
) -> Dict[str, Any]:
    """
    Train and save an LSTM model.
    
    Args:
        symbol: Asset symbol
        X: Feature matrix
        y: Target vector
        cache_dir: Directory to save model
        seq_length: Sequence length for LSTM
        batch_size: Training batch size
        epochs: Maximum training epochs
        learning_rate: Learning rate
        weight_decay: Weight decay for regularization
        patience: Early stopping patience
        hidden: LSTM hidden size
        layers: Number of LSTM layers
        dropout: Dropout rate
        
    Returns:
        Dictionary with training metrics and model path
    """
    if cache_dir is None:
        cache_dir = settings.model_cache_dir
    
    os.makedirs(cache_dir, exist_ok=True)
    
    device = torch.device(os.getenv("DEVICE", "cpu"))
    
    # Create sequences
    X_seq, y_seq = create_sequences(X, y, seq_length)
    
    if len(X_seq) < batch_size:
        raise ValueError(f"Not enough samples for training. Need at least {batch_size}, got {len(X_seq)}")
    
    # Split train/val (time-series split: last 20% for validation)
    split_idx = int(len(X_seq) * 0.8)
    X_train, X_val = X_seq[:split_idx], X_seq[split_idx:]
    y_train, y_val = y_seq[:split_idx], y_seq[split_idx:]
    
    # Create datasets and loaders
    train_dataset = PriceDataset(X_train, y_train, seq_length)
    val_dataset = PriceDataset(X_val, y_val, seq_length)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    input_size = X.shape[1]
    model = PriceLSTM(input_size, hidden, layers, dropout).to(device)
    
    # Loss and optimizer
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=3)
    
    # Training loop
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    logger.info(
        "Starting LSTM training",
        symbol=symbol,
        train_samples=len(train_dataset),
        val_samples=len(val_dataset),
        input_size=input_size
    )
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            predicted = (outputs > 0.5).float()
            train_total += batch_y.size(0)
            train_correct += (predicted == batch_y).sum().item()
        
        train_loss /= len(train_loader)
        train_acc = train_correct / train_total
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                
                val_loss += loss.item()
                predicted = (outputs > 0.5).float()
                val_total += batch_y.size(0)
                val_correct += (predicted == batch_y).sum().item()
        
        val_loss /= len(val_loader)
        val_acc = val_correct / val_total
        
        scheduler.step(val_loss)
        
        logger.debug(
            "Epoch completed",
            epoch=epoch + 1,
            train_loss=train_loss,
            train_acc=train_acc,
            val_loss=val_loss,
            val_acc=val_acc
        )
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(
                    "Early stopping triggered",
                    epoch=epoch + 1,
                    best_val_loss=best_val_loss
                )
                break
    
    # Load best model
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    # Save model
    safe_symbol = symbol.replace("/", "_")
    filename = f"{safe_symbol}_lstm.pt"
    path = os.path.join(cache_dir, filename)
    
    checkpoint = {
        "state_dict": model.state_dict(),
        "config": {
            "input_size": input_size,
            "hidden": hidden,
            "layers": layers,
            "dropout": dropout
        },
        "symbol": symbol,
        "model_type": "lstm",
        "training_samples": len(X_seq),
        "val_accuracy": val_acc,
        "val_loss": best_val_loss
    }
    
    torch.save(checkpoint, path)
    
    logger.info(
        "LSTM model saved",
        symbol=symbol,
        path=path,
        val_accuracy=val_acc,
        val_loss=best_val_loss
    )
    
    return {
        "val_accuracy": val_acc,
        "val_loss": best_val_loss,
        "path": path,
        "training_samples": len(X_seq),
        "epochs_trained": epoch + 1
    }


def load_model(symbol: str, cache_dir: Optional[str] = None) -> Optional[Tuple[PriceLSTM, Dict[str, Any]]]:
    """
    Load a trained LSTM model.
    
    Args:
        symbol: Asset symbol
        cache_dir: Directory containing saved models
        
    Returns:
        Tuple of (model, config) or None if not found
    """
    if cache_dir is None:
        cache_dir = settings.model_cache_dir
    
    safe_symbol = symbol.replace("/", "_")
    filename = f"{safe_symbol}_lstm.pt"
    path = os.path.join(cache_dir, filename)
    
    if not os.path.exists(path):
        logger.warning(
            "LSTM model file not found",
            symbol=symbol,
            path=path
        )
        return None
    
    try:
        checkpoint = torch.load(path, map_location="cpu")
        config = checkpoint["config"]
        
        model = PriceLSTM(**config)
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()
        
        logger.info(
            "LSTM model loaded",
            symbol=symbol,
            path=path
        )
        
        return model, checkpoint
    except Exception as e:
        logger.error(
            "Failed to load LSTM model",
            symbol=symbol,
            error=str(e)
        )
        return None


def predict(
    model: PriceLSTM,
    X: np.ndarray,
    seq_length: int = 30
) -> Dict[str, np.ndarray]:
    """
    Make predictions with a trained LSTM model.
    
    Args:
        model: Trained LSTM model
        X: Feature matrix
        seq_length: Sequence length
        
    Returns:
        Dictionary with predictions and confidence
    """
    device = torch.device("cpu")
    model = model.to(device)
    model.eval()
    
    # Create sequences
    X_seq, _ = create_sequences(X, np.zeros(len(X)), seq_length)
    X_tensor = torch.FloatTensor(X_seq).to(device)
    
    with torch.no_grad():
        outputs = model(X_tensor)
        probabilities = outputs.cpu().numpy()
        predictions = (probabilities > 0.5).astype(int)
        confidence = np.maximum(probabilities, 1 - probabilities)
    
    return {
        "predictions": predictions.flatten(),
        "probabilities": probabilities.flatten(),
        "confidence": confidence.flatten()
    }
