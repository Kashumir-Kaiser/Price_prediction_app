/**
 * Tests for AssetSelector component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AssetSelector } from '@/components/AssetSelector';

// Mock the store
vi.mock('@/store/useMarketStore', () => ({
  useMarketStore: () => ({
    selectedSymbol: 'BTC/USD',
    setSymbol: vi.fn(),
  }),
}));

describe('AssetSelector', () => {
  it('renders three tabs', () => {
    render(<AssetSelector />);
    
    expect(screen.getByText('Crypto')).toBeInTheDocument();
    expect(screen.getByText('Stable')).toBeInTheDocument();
    expect(screen.getByText('VN Stocks')).toBeInTheDocument();
  });

  it('shows crypto assets by default', () => {
    render(<AssetSelector />);
    
    expect(screen.getByText('Bitcoin')).toBeInTheDocument();
    expect(screen.getByText('Ethereum')).toBeInTheDocument();
    expect(screen.getByText('Solana')).toBeInTheDocument();
  });

  it('calls onSelect when clicking a crypto asset', () => {
    const mockOnSelect = vi.fn();
    render(<AssetSelector onSelect={mockOnSelect} />);
    
    fireEvent.click(screen.getByText('Bitcoin'));
    
    expect(mockOnSelect).toHaveBeenCalledWith('BTC/USD', 'crypto');
  });

  it('switches to stable tab when clicked', () => {
    render(<AssetSelector />);
    
    fireEvent.click(screen.getByText('Stable'));
    
    expect(screen.getByText('Tether')).toBeInTheDocument();
    expect(screen.getByText('USD Coin')).toBeInTheDocument();
  });

  it('switches to stocks tab when clicked', () => {
    render(<AssetSelector />);
    
    fireEvent.click(screen.getByText('VN Stocks'));
    
    expect(screen.getByText('Vinamilk')).toBeInTheDocument();
    expect(screen.getByText('Vingroup')).toBeInTheDocument();
  });

  it('filters stocks based on search input', () => {
    render(<AssetSelector />);
    
    fireEvent.click(screen.getByText('VN Stocks'));
    
    const searchInput = screen.getByPlaceholderText('Search stocks...');
    fireEvent.change(searchInput, { target: { value: 'VNM' } });
    
    expect(screen.getByText('Vinamilk')).toBeInTheDocument();
    expect(screen.queryByText('FPT Corp')).not.toBeInTheDocument();
  });
});
