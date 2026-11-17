package com.labcare.security;

import com.labcare.common.BusinessException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 统一鉴权拦截器：
 * 1. 放行登录、健康检查与预检请求；
 * 2. /internal/** 使用服务间令牌，供 AI 服务调用业务工具；
 * 3. 其余接口必须携带有效 Bearer Token，/admin/** 必须是管理员。
 */
@Component
public class AuthInterceptor implements HandlerInterceptor {

    private final JwtUtil jwtUtil;
    private final String internalToken;

    public AuthInterceptor(JwtUtil jwtUtil, @Value("${labcare.ai.internal-token:}") String internalToken) {
        this.jwtUtil = jwtUtil;
        this.internalToken = internalToken;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        String path = request.getRequestURI().substring(request.getContextPath().length());
        if (path.startsWith("/internal/")) {
            String token = request.getHeader("X-Internal-Token");
            if (internalToken.isBlank() || !internalToken.equals(token)) {
                throw BusinessException.forbidden("服务间令牌无效");
            }
            UserContext.set(new CurrentUser(0L, "ai-service", "AI 服务", "SYSTEM"));
            return true;
        }

        String header = request.getHeader("Authorization");
        String token = header != null && header.startsWith("Bearer ") ? header.substring(7).trim() : null;
        CurrentUser user = jwtUtil.parse(token);
        if (user == null) {
            throw BusinessException.unauthorized("登录状态已失效，请重新登录");
        }
        if (path.startsWith("/admin/") && !user.isAdmin()) {
            throw BusinessException.forbidden("无权访问管理员接口");
        }
        UserContext.set(user);
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        UserContext.clear();
    }
}
