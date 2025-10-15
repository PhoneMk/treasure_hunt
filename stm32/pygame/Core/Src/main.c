/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "rng.h"
#include "spi.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "stdio.h"
#include "string.h"

#include "ILI9341_GFX.h"
#include "ILI9341_STM32_Driver.h"
#include "ILI9341_Touchscreen.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
#define ILI9341_COLOR565(r,g,b) ( ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b) >> 3) )

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
uint8_t rx_buffer[100];
uint8_t echo_buffer[100];
static uint8_t rx_index = 0;
uint8_t byte;
volatile uint8_t command_ready = 0;  // Flag when full command received
volatile uint8_t command_length = 0;
volatile uint8_t led_blink_flag = 0;
volatile uint8_t buzz_flag = 0;
volatile uint8_t joystick_flag = 0;
uint16_t x;
uint16_t y;
volatile uint32_t readValue [2];
uint8_t state;
uint16_t deadzone = 50;
uint16_t mid_x = 3100;
uint16_t mid_y = 3100;

int food_count = 0;
int energy_level = 0;
char status_msg[50] = "Ready";


char b [50];

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
void Set_Buzzer_PWM(uint16_t duty);
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* Enable the CPU Cache */

  /* Enable I-Cache---------------------------------------------------------*/
  SCB_EnableICache();

  /* Enable D-Cache---------------------------------------------------------*/
  SCB_EnableDCache();

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_USART3_UART_Init();
  MX_ADC1_Init();
  MX_RNG_Init();
  MX_SPI5_Init();
  MX_TIM1_Init();
  MX_TIM2_Init();
  /* USER CODE BEGIN 2 */
  ILI9341_Init();
  HAL_ADC_Start_DMA(&hadc1, (uint32_t*)readValue, 2);
  HAL_UART_Receive_IT(&huart3, &byte, 1);
  HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_4);


  ILI9341_Set_Rotation(SCREEN_HORIZONTAL_2);
//  ILI9341_Fill_Screen(BLACK);
//  ILI9341_Draw_Text("Treasure Hunt Ready!", 10, 10, WHITE, 2, BLACK);
//  ILI9341_Draw_Text("Food: 0", 10, 40, GREEN, 2, BLACK);
//  ILI9341_Draw_Text("Energy: 100", 10, 70, YELLOW, 2, BLACK);

  // Draw dashboard frame
  ILI9341_Fill_Screen(BLACK);

  // Title
  ILI9341_Draw_Text("Treasure Hunt", 10, 10, WHITE, 2, BLACK);

  // Food Box
  ILI9341_Draw_Filled_Rectangle_Coord(10, 40, 310, 70, DARKGREEN);
  ILI9341_Draw_Text("Food: 0", 15, 45, WHITE, 2, DARKGREEN);

  // Energy Box
  ILI9341_Draw_Filled_Rectangle_Coord(10, 75, 310, 105, DARKYELLOW);
  ILI9341_Draw_Text("Energy: 100", 15, 80, WHITE, 2, DARKYELLOW);

  // Status Box
  ILI9341_Draw_Filled_Rectangle_Coord(10, 110, 310, 140, DARKCYAN);
  ILI9341_Draw_Text("Status: Ready", 15, 115, WHITE, 2, DARKCYAN);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {

	  if (command_ready) {
	       // Echo back for testing with clear formatting
	       HAL_UART_Transmit(&huart3, echo_buffer, command_length, 100);
	       char buffer[50];
	       // Update Food value
	          ILI9341_Draw_Filled_Rectangle_Coord(80, 45, 220, 65, DARKGREEN);
	          sprintf(buffer, "%d", food_count);
	          ILI9341_Draw_Text(buffer, 80, 45, GREEN, 2, DARKGREEN);

	          // Update Energy value
	          ILI9341_Draw_Filled_Rectangle_Coord(90, 80, 220, 100, DARKYELLOW);
	          sprintf(buffer, "%d", energy_level);
	          ILI9341_Draw_Text(buffer, 100, 80, YELLOW, 2, DARKYELLOW);

	          // Update Status
	          ILI9341_Draw_Filled_Rectangle_Coord(90, 115, 300, 135, DARKCYAN);
	          ILI9341_Draw_Text(status_msg, 100, 115, CYAN, 2, DARKCYAN);
	       command_ready = 0;
	     }

	  if (buzz_flag)
	  {
		  Set_Buzzer_PWM(50);   // 50% duty cycle, adjust volume
		  HAL_Delay(300);
		  Set_Buzzer_PWM(0);    // Turn off buzzer
		  buzz_flag = 0;
	  }

	    if (led_blink_flag) {
	        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_SET);
	        HAL_Delay(300);
	        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET);
	        led_blink_flag = 0;
	    }
	  if (joystick_flag) {
		  x = (uint16_t) readValue[0];
		  y = (uint16_t) readValue[1];

		  state = HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_0);
		  joystick_flag = 0;
	//	  sprintf(b, "X : %d, Y : %d, button: %d\r\n" ,x, y, state);
	//	  HAL_UART_Transmit(&huart3, (uint8_t*)b, strlen(b), HAL_MAX_DELAY);
	//	  HAL_Delay(300);

		  char dir = 'N'; // N = Neutral / no movement

		 if (x > mid_x + deadzone)
			 dir = 'R'; // right
		 else if (x < mid_x - deadzone)
			 dir = 'L'; // left
		 else if (y > mid_y + deadzone)
			 dir = 'U'; // up
		 else if (y < mid_y - deadzone)
			 dir = 'D'; // down

		 // Send only if movement detected
		 if (dir != 'N')
		 {
			char msg[3] = {dir, '\r', '\n'};
			HAL_UART_Transmit(&huart3, (uint8_t*)msg, 3, HAL_MAX_DELAY);
		 }

		 // Send button state if pressed
		 if (state == GPIO_PIN_RESET)
		 {
			char msg[3] = {'B', '\r', '\n'};
			HAL_UART_Transmit(&huart3, (uint8_t*)msg, 3, HAL_MAX_DELAY);
		 }
	  }
	HAL_Delay(200);




    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSI;
  RCC_OscInitStruct.PLL.PLLM = 8;
  RCC_OscInitStruct.PLL.PLLN = 216;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Activate the Over-Drive mode
  */
  if (HAL_PWREx_EnableOverDrive() != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_7) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
void Set_Buzzer_PWM(uint16_t duty) {
    // duty: 0-100 for 0% to 100%
    if(duty > 100) duty = 100;
    __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_4, (htim2.Init.Period + 1) * duty / 100);
}
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
    if(hadc->Instance == ADC1)
    {
        // Joystick values are ready in readValue array
        joystick_flag = 1;
        // Process joystick input here
    }
}
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
	  if (huart->Instance == USART3)
	  {
	    rx_buffer[rx_index++] = byte;

	    // Check for end of message
	    if (byte == '\n' || rx_index >= sizeof(rx_buffer)-1) {
	      led_blink_flag = 1;  // Visual confirmation

	      rx_buffer[rx_index] = '\0';
	      memcpy(echo_buffer, rx_buffer, rx_index);
	      command_length = rx_index;
	      if (rx_buffer[0] == 'F' && rx_buffer[1] == ':') {
			  food_count = atoi((char*)&rx_buffer[2]);
		      command_ready = 1;
		      buzz_flag = 1;
		  }
		  else if (rx_buffer[0] == 'E' && rx_buffer[1] == ':') {
			  energy_level = atoi((char*)&rx_buffer[2]);
		      command_ready = 1;
		  }
		  else if (rx_buffer[0] == 'S' && rx_buffer[1] == ':') {
			  strcpy(status_msg, (char*)&rx_buffer[2]);
		      command_ready = 1;
		      buzz_flag = 1;
		  }
	      rx_index = 0;
	    }

	    HAL_UART_Receive_IT(&huart3, &byte, 1);
    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
