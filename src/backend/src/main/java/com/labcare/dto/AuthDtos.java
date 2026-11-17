package com.labcare.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * 认证相关 DTO。
 */
public final class AuthDtos {

    private AuthDtos() {
    }

    public record LoginRequest(
            @NotBlank(message = "不能为空") String username,
            @NotBlank(message = "不能为空") String password) {
    }

    public record UserView(Long id, String username, String displayName, String role, String roleLabel) {
    }

    public record LoginResponse(String token, UserView user) {
    }
}
