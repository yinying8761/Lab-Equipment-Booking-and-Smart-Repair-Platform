package com.labcare.common;

import java.time.LocalDateTime;

/**
 * 统一响应结构：前端只需判断 code == 0。
 */
public record ApiResponse<T>(int code, String message, T data, LocalDateTime timestamp) {

    public static <T> ApiResponse<T> ok(T data) {
        return new ApiResponse<>(0, "success", data, LocalDateTime.now());
    }

    public static ApiResponse<Void> ok() {
        return new ApiResponse<>(0, "success", null, LocalDateTime.now());
    }

    public static <T> ApiResponse<T> fail(int code, String message) {
        return new ApiResponse<>(code, message, null, LocalDateTime.now());
    }
}
