package com.labcare.security;

import com.labcare.common.BusinessException;

/**
 * 请求级用户上下文。业务代码通过 {@link #require()} 获取当前用户，
 * 所有数据归属判断都以此为准，避免信任前端传入的用户 id。
 */
public final class UserContext {

    private static final ThreadLocal<CurrentUser> HOLDER = new ThreadLocal<>();

    private UserContext() {
    }

    public static void set(CurrentUser user) {
        HOLDER.set(user);
    }

    public static CurrentUser current() {
        return HOLDER.get();
    }

    public static CurrentUser require() {
        CurrentUser user = HOLDER.get();
        if (user == null) {
            throw BusinessException.unauthorized("登录状态已失效，请重新登录");
        }
        return user;
    }

    public static void clear() {
        HOLDER.remove();
    }
}
