package com.labcare.security;

/**
 * 当前登录用户，由拦截器解析 JWT 后写入线程上下文。
 */
public record CurrentUser(Long id, String username, String displayName, String role) {

    public boolean isAdmin() {
        return "ADMIN".equals(role);
    }
}
