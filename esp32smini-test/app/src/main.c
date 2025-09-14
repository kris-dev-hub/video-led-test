#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/rmt_tx.h"
#include "esp_log.h"
#include "esp_err.h"

#define LED_PIN 21
#define RMT_LED_STRIP_RESOLUTION_HZ 10000000 // 10MHz resolution, 1 tick = 0.1us

static const char *TAG = "green_led_blink";

typedef struct {
    uint8_t level0;
    uint8_t level1;
    uint16_t duration0;
    uint16_t duration1;
} led_strip_encoder_config_t;

static rmt_channel_handle_t led_chan = NULL;
static rmt_encoder_handle_t led_encoder = NULL;

// WS2812 timing (in 0.1us units)
#define WS2812_T0H_NS (350)    // 0 code high level time (0.35us)
#define WS2812_T0L_NS (800)    // 0 code low level time (0.8us)
#define WS2812_T1H_NS (700)    // 1 code high level time (0.7us)
#define WS2812_T1L_NS (600)    // 1 code low level time (0.6us)

static uint8_t led_data[3]; // GRB format for WS2812

static void send_led_data(uint8_t red, uint8_t green, uint8_t blue)
{
    // WS2812 uses GRB format
    led_data[0] = green;
    led_data[1] = red;
    led_data[2] = blue;

    rmt_symbol_word_t symbols[24]; // 8 bits * 3 colors = 24 symbols

    for (int i = 0; i < 3; i++) {
        for (int j = 7; j >= 0; j--) {
            int bit = (led_data[i] >> j) & 1;
            int symbol_idx = i * 8 + (7 - j);

            if (bit) {
                // Send '1' bit: high for 0.7us, low for 0.6us
                symbols[symbol_idx].level0 = 1;
                symbols[symbol_idx].duration0 = 7; // 0.7us
                symbols[symbol_idx].level1 = 0;
                symbols[symbol_idx].duration1 = 6; // 0.6us
            } else {
                // Send '0' bit: high for 0.35us, low for 0.8us
                symbols[symbol_idx].level0 = 1;
                symbols[symbol_idx].duration0 = 4; // 0.4us (close to 0.35us)
                symbols[symbol_idx].level1 = 0;
                symbols[symbol_idx].duration1 = 8; // 0.8us
            }
        }
    }

    rmt_transmit_config_t tx_config = {
        .loop_count = 0,
    };

    ESP_ERROR_CHECK(rmt_transmit(led_chan, led_encoder, symbols, sizeof(symbols), &tx_config));
    ESP_ERROR_CHECK(rmt_tx_wait_all_done(led_chan, portMAX_DELAY));

    // Reset signal (low for > 50us)
    vTaskDelay(pdMS_TO_TICKS(1));
}

static void configure_rmt(void)
{
    ESP_LOGI(TAG, "Creating RMT TX channel for LED on GPIO %d", LED_PIN);

    rmt_tx_channel_config_t tx_chan_config = {
        .clk_src = RMT_CLK_SRC_DEFAULT,
        .gpio_num = LED_PIN,
        .mem_block_symbols = 64,
        .resolution_hz = RMT_LED_STRIP_RESOLUTION_HZ,
        .trans_queue_depth = 4,
    };
    ESP_ERROR_CHECK(rmt_new_tx_channel(&tx_chan_config, &led_chan));
    ESP_ERROR_CHECK(rmt_enable(led_chan));

    // Create a simple copy encoder
    rmt_copy_encoder_config_t encoder_config = {};
    ESP_ERROR_CHECK(rmt_new_copy_encoder(&encoder_config, &led_encoder));
}

void app_main(void)
{
    ESP_LOGI(TAG, "Starting Green LED Blink Application");

    configure_rmt();

    while (1) {
        ESP_LOGI(TAG, "Turning LED GREEN ON for 3 seconds");
        send_led_data(0, 255, 0); // Red=0, Green=255, Blue=0
        vTaskDelay(pdMS_TO_TICKS(3000));

        ESP_LOGI(TAG, "Turning LED OFF for 1 second");
        send_led_data(0, 0, 0); // All off
        vTaskDelay(pdMS_TO_TICKS(1000));

        // Try red for debug
        ESP_LOGI(TAG, "Turning LED RED ON for 2 seconds");
        send_led_data(255, 0, 0); // Red=255, Green=0, Blue=0
        vTaskDelay(pdMS_TO_TICKS(2000));

        ESP_LOGI(TAG, "Turning LED OFF for 1 second");
        send_led_data(0, 0, 0); // All off
        vTaskDelay(pdMS_TO_TICKS(1000));

        // Try blue for debug
        ESP_LOGI(TAG, "Turning LED BLUE ON for 2 seconds");
        send_led_data(0, 0, 255); // Red=0, Green=0, Blue=255
        vTaskDelay(pdMS_TO_TICKS(2000));

        ESP_LOGI(TAG, "Turning LED OFF for 1 second");
        send_led_data(0, 0, 0); // All off
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}