package alpaca

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

const BaseURL = "https://data.alpaca.markets/v1beta3/crypto/us"

type Bar struct {
	Timestamp time.Time `json:"t"`
	Open      float64   `json:"o"`
	High      float64   `json:"h"`
	Low       float64   `json:"l"`
	Close     float64   `json:"c"`
	Volume    float64   `json:"v"`
	VWAP      float64   `json:"vw"`
}

type Client struct {
	http      *http.Client
	APIKey    string
	SecretKey string
}

func NewClient(apiKey, secretKey string) *Client {
	return &Client{
		http:      &http.Client{Timeout: 30 * time.Second},
		APIKey:    apiKey,
		SecretKey: secretKey,
	}
}

// FetchLatestBar fetches the most recent daily bar for a symbol.
func (c *Client) FetchLatestBar(ctx context.Context, symbol string) ([]Bar, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", fmt.Sprintf("%s/bars", BaseURL), nil)
	if err != nil {
		return nil, err
	}
	q := req.URL.Query()
	q.Set("symbols", symbol)
	q.Set("timeframe", "1Day")
	q.Set("limit", "1")
	req.URL.RawQuery = q.Encode()
	req.Header.Set("APCA-API-KEY-ID", c.APIKey)
	req.Header.Set("APCA-API-SECRET-KEY", c.SecretKey)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("alpaca API returned %d", resp.StatusCode)
	}

	var payload struct {
		Bars map[string][]Bar `json:"bars"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, err
	}
	return payload.Bars[symbol], nil
}
