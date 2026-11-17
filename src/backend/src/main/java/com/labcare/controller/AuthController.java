package com.labcare.controller;

import com.labcare.common.ApiResponse;
import com.labcare.dto.AuthDtos;
import com.labcare.security.UserContext;
import com.labcare.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public ApiResponse<AuthDtos.LoginResponse> login(@Valid @RequestBody AuthDtos.LoginRequest request) {
        return ApiResponse.ok(authService.login(request));
    }

    @GetMapping("/me")
    public ApiResponse<AuthDtos.UserView> me() {
        return ApiResponse.ok(authService.me(UserContext.require()));
    }

    /** 前端丢弃本地令牌即可；接口保留用于统一交互与留痕。 */
    @PostMapping("/logout")
    public ApiResponse<Map<String, Object>> logout() {
        return ApiResponse.ok(Map.of("loggedOut", true));
    }
}
