package com.labcare;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 实验室设备预约与智能报修平台 —— 业务后端入口。
 */
@SpringBootApplication
@EnableScheduling
public class LabCareApplication {

    public static void main(String[] args) {
        SpringApplication.run(LabCareApplication.class, args);
    }
}
