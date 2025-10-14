package DrawBlocks

import (
	"context"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"os"

	"github.com/plobin/genkitgo/internal/models"
	"golang.org/x/image/font"
	"golang.org/x/image/font/basicfont"
	"golang.org/x/image/math/fixed"
)

type Service struct{}

func NewService() *Service {
	return &Service{}
}

// Execute draws OCR blocks on the original image and saves as visualization.png
func (s *Service) Execute(ctx context.Context, imagePath string, blocks []models.BlockInfo, outputPath string) error {
	// Load original image
	file, err := os.Open(imagePath)
	if err != nil {
		return fmt.Errorf("failed to open image: %w", err)
	}
	defer file.Close()

	img, _, err := image.Decode(file)
	if err != nil {
		return fmt.Errorf("failed to decode image: %w", err)
	}

	// Create RGBA image for drawing
	bounds := img.Bounds()
	rgba := image.NewRGBA(bounds)
	draw.Draw(rgba, bounds, img, bounds.Min, draw.Src)

	// Draw each block
	for _, block := range blocks {
		s.drawBlock(rgba, block)
	}

	// Save visualization
	outFile, err := os.Create(outputPath)
	if err != nil {
		return fmt.Errorf("failed to create output file: %w", err)
	}
	defer outFile.Close()

	if err := png.Encode(outFile, rgba); err != nil {
		return fmt.Errorf("failed to encode image: %w", err)
	}

	return nil
}

// drawBlock draws a single block on the image
func (s *Service) drawBlock(img *image.RGBA, block models.BlockInfo) {
	// Define colors
	rectColor := color.RGBA{R: 0, G: 255, B: 0, A: 255}      // Green for rectangle
	textColor := color.RGBA{R: 255, G: 0, B: 0, A: 255}      // Red for text
	lowConfColor := color.RGBA{R: 255, G: 165, B: 0, A: 255} // Orange for low confidence

	// Choose color based on confidence
	boxColor := rectColor
	if block.Confidence < 0.8 {
		boxColor = lowConfColor
	}

	// Draw rectangle around block
	x1 := block.BBox.X
	y1 := block.BBox.Y
	x2 := x1 + block.BBox.Width
	y2 := y1 + block.BBox.Height

	// Draw top line
	s.drawHorizontalLine(img, x1, y1, x2, boxColor)
	// Draw bottom line
	s.drawHorizontalLine(img, x1, y2, x2, boxColor)
	// Draw left line
	s.drawVerticalLine(img, x1, y1, y2, boxColor)
	// Draw right line
	s.drawVerticalLine(img, x2, y1, y2, boxColor)

	// Draw block ID at top-left corner
	s.drawText(img, x1+2, y1-2, fmt.Sprintf("#%d", block.ID), textColor)
}

// drawHorizontalLine draws a horizontal line
func (s *Service) drawHorizontalLine(img *image.RGBA, x1, y, x2 int, col color.RGBA) {
	for x := x1; x <= x2; x++ {
		img.Set(x, y, col)
		img.Set(x, y+1, col) // Make line thicker
	}
}

// drawVerticalLine draws a vertical line
func (s *Service) drawVerticalLine(img *image.RGBA, x, y1, y2 int, col color.RGBA) {
	for y := y1; y <= y2; y++ {
		img.Set(x, y, col)
		img.Set(x+1, y, col) // Make line thicker
	}
}

// drawText draws text on the image
func (s *Service) drawText(img *image.RGBA, x, y int, text string, col color.RGBA) {
	point := fixed.Point26_6{X: fixed.Int26_6(x * 64), Y: fixed.Int26_6(y * 64)}

	d := &font.Drawer{
		Dst:  img,
		Src:  image.NewUniform(col),
		Face: basicfont.Face7x13,
		Dot:  point,
	}
	d.DrawString(text)
}
