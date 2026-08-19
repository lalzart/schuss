#pragma once

#include "schuss_rt/runtime_v1.hpp"

#include <atomic>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>

namespace schuss::rt::v1 {

static_assert(std::atomic<Runtime*>::is_always_lock_free);
static_assert(std::atomic<std::uint64_t>::is_always_lock_free);

struct ReplacementResult {
    bool ok{};
    const char* code{"HOST_V1_REPLACEMENT_FAILED"};

    operator bool() const noexcept { return ok; }
};

struct ReplacementTelemetry {
    std::string old_package_content_hash;
    std::string new_package_content_hash;
    std::uint64_t activation_generation{};
    const char* state_policy{"reset-state"};
    const char* activation_boundary{"audio-block-boundary"};
};

class RuntimeReplacementSlot {
public:
    RuntimeReplacementSlot() = default;
    RuntimeReplacementSlot(const RuntimeReplacementSlot&) = delete;
    RuntimeReplacementSlot& operator=(const RuntimeReplacementSlot&) = delete;

    ReplacementResult install_initial(
        std::unique_ptr<Runtime> runtime, std::string package_content_hash
    ) {
        if (!runtime || !runtime->prepared()
            || runtime->package().content_hash != package_content_hash
            || active_owner_ || pending_owner_) {
            return {false, "HOST_V1_INITIAL_RUNTIME_INVALID"};
        }
        active_hash_ = std::move(package_content_hash);
        active_owner_ = std::move(runtime);
        active_.store(active_owner_.get(), std::memory_order_release);
        generation_.store(1, std::memory_order_release);
        return {true, "ok"};
    }

    ReplacementResult prepare_successor(
        std::unique_ptr<Runtime> runtime,
        std::string package_content_hash,
        std::uint64_t expected_generation,
        std::string_view expected_active_hash
    ) {
        if (!runtime || !runtime->prepared()
            || runtime->package().content_hash != package_content_hash) {
            return {false, "HOST_V1_REPLACEMENT_RUNTIME_INVALID"};
        }
        if (!active_owner_ || generation() != expected_generation) {
            return {false, "HOST_V1_REPLACEMENT_GENERATION_STALE"};
        }
        if (active_hash_ != expected_active_hash) {
            return {false, "HOST_V1_REPLACEMENT_ACTIVE_HASH_STALE"};
        }
        if (pending_owner_ || requested_.load(std::memory_order_acquire) != nullptr
            || activated_.load(std::memory_order_acquire) != nullptr) {
            return {false, "HOST_V1_REPLACEMENT_ALREADY_PENDING"};
        }
        pending_hash_ = std::move(package_content_hash);
        pending_owner_ = std::move(runtime);
        return {true, "ok"};
    }

    ReplacementResult request_activation(
        std::uint64_t expected_generation,
        std::string_view expected_active_hash,
        std::string_view expected_successor_hash
    ) noexcept {
        if (!pending_owner_) return {false, "HOST_V1_REPLACEMENT_NOT_PREPARED"};
        if (generation() != expected_generation) {
            return {false, "HOST_V1_REPLACEMENT_GENERATION_STALE"};
        }
        if (active_hash_ != expected_active_hash) {
            return {false, "HOST_V1_REPLACEMENT_ACTIVE_HASH_STALE"};
        }
        if (pending_hash_ != expected_successor_hash) {
            return {false, "HOST_V1_REPLACEMENT_SUCCESSOR_HASH_STALE"};
        }
        activation_requested_.store(true, std::memory_order_release);
        Runtime* expected = nullptr;
        if (!requested_.compare_exchange_strong(
                expected,
                pending_owner_.get(),
                std::memory_order_release,
                std::memory_order_relaxed
            )) {
            activation_requested_.store(false, std::memory_order_release);
            return {false, "HOST_V1_REPLACEMENT_ALREADY_PENDING"};
        }
        return {true, "ok"};
    }

    Runtime* begin_block() noexcept {
        Runtime* successor = requested_.exchange(nullptr, std::memory_order_acq_rel);
        if (successor != nullptr) {
            Runtime* retired = active_.exchange(successor, std::memory_order_acq_rel);
            retired_.store(retired, std::memory_order_release);
            generation_.fetch_add(1, std::memory_order_acq_rel);
            activated_.store(successor, std::memory_order_release);
        }
        return active_.load(std::memory_order_acquire);
    }

    bool activation_observed() const noexcept {
        return pending_owner_
            && activated_.load(std::memory_order_acquire) == pending_owner_.get();
    }

    ReplacementResult complete_activation(ReplacementTelemetry& telemetry) {
        if (!activation_observed()
            || retired_.load(std::memory_order_acquire) != active_owner_.get()) {
            return {false, "HOST_V1_REPLACEMENT_NOT_ACTIVATED"};
        }
        telemetry.old_package_content_hash = active_hash_;
        telemetry.new_package_content_hash = pending_hash_;
        telemetry.activation_generation = generation();
        std::unique_ptr<Runtime> retired_owner = std::move(active_owner_);
        active_owner_ = std::move(pending_owner_);
        active_hash_ = std::move(pending_hash_);
        activation_requested_.store(false, std::memory_order_release);
        activated_.store(nullptr, std::memory_order_release);
        retired_.store(nullptr, std::memory_order_release);
        retired_owner.reset();
        return {true, "ok"};
    }

    ReplacementResult cancel_pending() {
        if (!pending_owner_) return {false, "HOST_V1_REPLACEMENT_NOT_PREPARED"};
        if (activated_.load(std::memory_order_acquire) != nullptr) {
            return {false, "HOST_V1_REPLACEMENT_ALREADY_ACTIVATED"};
        }
        if (!activation_requested_.load(std::memory_order_acquire)) {
            pending_owner_.reset();
            pending_hash_.clear();
            return {true, "ok"};
        }
        Runtime* expected = pending_owner_.get();
        if (!requested_.compare_exchange_strong(
                expected,
                nullptr,
                std::memory_order_acq_rel,
                std::memory_order_acquire
            )) {
            return {false, "HOST_V1_REPLACEMENT_ACTIVATION_RACE"};
        }
        activation_requested_.store(false, std::memory_order_release);
        pending_owner_.reset();
        pending_hash_.clear();
        return {true, "ok"};
    }

    Runtime* active() const noexcept {
        return active_.load(std::memory_order_acquire);
    }

    std::uint64_t generation() const noexcept {
        return generation_.load(std::memory_order_acquire);
    }

    const std::string& active_hash() const noexcept { return active_hash_; }
    const std::string& pending_hash() const noexcept { return pending_hash_; }
    bool has_pending() const noexcept { return pending_owner_ != nullptr; }

    void clear_after_callback_stopped() {
        requested_.store(nullptr, std::memory_order_release);
        activation_requested_.store(false, std::memory_order_release);
        activated_.store(nullptr, std::memory_order_release);
        retired_.store(nullptr, std::memory_order_release);
        active_.store(nullptr, std::memory_order_release);
        pending_owner_.reset();
        active_owner_.reset();
        pending_hash_.clear();
        active_hash_.clear();
        generation_.store(0, std::memory_order_release);
    }

private:
    std::unique_ptr<Runtime> active_owner_;
    std::unique_ptr<Runtime> pending_owner_;
    std::string active_hash_;
    std::string pending_hash_;
    std::atomic<Runtime*> active_{nullptr};
    std::atomic<Runtime*> requested_{nullptr};
    std::atomic<bool> activation_requested_{false};
    std::atomic<Runtime*> activated_{nullptr};
    std::atomic<Runtime*> retired_{nullptr};
    std::atomic<std::uint64_t> generation_{0};
};

}  // namespace schuss::rt::v1
