/**
 * Tests for PredictionCard component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PredictionCard } from '@/components/PredictionCard';
import { Prediction } from '@/types/market';

const mockPrediction: Prediction = {
  symbol: 'BTC/USD',
  asset_type: 'crypto',
  model: 'rf',
  predicted_close: 45000.50,
  direction: 'up',
  confidence: 0.75,
  horizon: '1D',
  generated_at: '2024-01-15T09:00:00Z',
  features_used: ['close_lag1', 'rsi_14', 'macd_signal'],
};

describe('PredictionCard', () => {
  it('renders loading state', () => {
    render(<PredictionCard modelName="rf" isLoading={true} />);
    
    // Should show skeleton/loading elements
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders no prediction available state', () => {
    render(<PredictionCard modelName="rf" isLoading={false} />);
    
    expect(screen.getByText('No prediction available')).toBeInTheDocument();
    expect(screen.getByText('Model may need training')).toBeInTheDocument();
  });

  it('renders prediction with correct direction badge', () => {
    render(<PredictionCard prediction={mockPrediction} modelName="rf" />);
    
    expect(screen.getByText('UP')).toBeInTheDocument();
    expect(screen.getByText('Random Forest')).toBeInTheDocument();
  });

  it('displays predicted close price', () => {
    render(<PredictionCard prediction={mockPrediction} modelName="rf" />);
    
    expect(screen.getByText('$45,000.50')).toBeInTheDocument();
  });

  it('displays confidence percentage', () => {
    render(<PredictionCard prediction={mockPrediction} modelName="rf" />);
    
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('shows key features', () => {
    render(<PredictionCard prediction={mockPrediction} modelName="rf" />);
    
    expect(screen.getByText('close_lag1')).toBeInTheDocument();
    expect(screen.getByText('rsi_14')).toBeInTheDocument();
  });

  it('renders down direction with correct styling', () => {
    const downPrediction = { ...mockPrediction, direction: 'down' as const };
    render(<PredictionCard prediction={downPrediction} modelName="rf" />);
    
    expect(screen.getByText('DOWN')).toBeInTheDocument();
  });

  it('renders flat direction with correct styling', () => {
    const flatPrediction = { ...mockPrediction, direction: 'flat' as const };
    render(<PredictionCard prediction={flatPrediction} modelName="rf" />);
    
    expect(screen.getByText('FLAT')).toBeInTheDocument();
  });
});
