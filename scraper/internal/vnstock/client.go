package vnstock

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

const SidecarURL = "http://vnstock-sidecar:9001"

type Client struct {
	http *http.Client
	base string
}

func NewClient() *Client {
	return &Client{
		http: &http.Client{Timeout: 30 * time.Second},
		base: SidecarURL,
	}
}

type OHLCV struct {
	Ts     string  `json:"ts"`
	Open   float64 `json:"open"`
	High   float64 `json:"high"`
	Low    float64 `json:"low"`
	Close  float64 `json:"close"`
	Volume float64 `json:"volume"`
}

// FetchOHLCV fetches daily OHLCV bars from the vnstock sidecar.
func (c *Client) FetchOHLCV(ctx context.Context, symbol string) ([]OHLCV, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", fmt.Sprintf("%s/ohlcv", c.base), nil)
	if err != nil {
		return nil, err
	}
	q := req.URL.Query()
	q.Set("symbol", symbol)
	q.Set("start", time.Now().AddDate(0, 0, -30).Format("2006-01-02"))
	q.Set("end", time.Now().Format("2006-01-02"))
	req.URL.RawQuery = q.Encode()

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("vnstock sidecar returned %d", resp.StatusCode)
	}

	var bars []OHLCV
	if err := json.NewDecoder(resp.Body).Decode(&bars); err != nil {
		return nil, err
	}
	return bars, nil
}
