/**
 * licensing.js - Handles licensing UI functionality
 * For Nova Sounds Shorts Machine
 */

// Licensing Tab Functions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize licensing tab
    initializeLicensingTab();

    // Add event listener for the licensing tab
    document.getElementById('licensing-tab').addEventListener('shown.bs.tab', fetchLicenseData);
});

// Initialize licensing tab functionality
function initializeLicensingTab() {
    // Add event listeners for licensing tab buttons
    document.getElementById('viewLicenseKeyBtn').addEventListener('click', toggleLicenseKeyVisibility);
    document.getElementById('renewLicenseBtn').addEventListener('click', handleRenewLicense);
    document.getElementById('upgradeLicenseBtn').addEventListener('click', handleUpgradeLicense);
    document.getElementById('transferLicenseBtn').addEventListener('click', handleTransferLicense);
    document.getElementById('viewAllPlansBtn').addEventListener('click', handleViewAllPlans);
    document.getElementById('manageDevicesBtn').addEventListener('click', handleManageDevices);
    document.getElementById('importMusicRightsBtn').addEventListener('click', handleImportMusicRights);
    document.getElementById('exportMusicRightsBtn').addEventListener('click', handleExportMusicRights);
    document.getElementById('manageLicenseTagsBtn').addEventListener('click', handleManageLicenseTags);
    document.getElementById('copyReferralBtn').addEventListener('click', handleCopyReferralLink);
    document.getElementById('affiliateDashboardBtn').addEventListener('click', handleAffiliateDashboard);
    document.getElementById('disableAutoRenewalBtn').addEventListener('click', handleDisableAutoRenewal);
    document.getElementById('updatePaymentMethodBtn').addEventListener('click', handleUpdatePaymentMethod);
    
    // Add event listeners to music rights table buttons
    document.querySelectorAll('#musicRightsTableBody button').forEach(button => {
        button.addEventListener('click', () => {
            handleEditMusicRights(button.getAttribute('data-track'));
        });
    });

    // Initialize toggle functionality
    document.getElementById('autoTagToggle').addEventListener('change', handleAutoTagToggle);
}

// Toggle license key visibility (show/hide)
function toggleLicenseKeyVisibility() {
    const licenseKeyInput = document.getElementById('licenseKey');
    const viewButton = document.getElementById('viewLicenseKeyBtn');
    
    if (licenseKeyInput.value === 'XXXX-XXXX-XXXX-XXXX') {
        // Simulate fetching the actual license key
        licenseKeyInput.value = 'ABCD-EF12-GH34-IJ56';
        viewButton.innerHTML = '<i class="bi bi-eye-slash"></i>';
    } else {
        licenseKeyInput.value = 'XXXX-XXXX-XXXX-XXXX';
        viewButton.innerHTML = '<i class="bi bi-eye"></i>';
    }
}

// Fetch license data from the server
function fetchLicenseData() {
    // Simulate API call with a timeout
    document.getElementById('licenseStatusMessage').innerHTML = '<i class="bi bi-arrow-repeat spin me-2"></i> Loading license information...';
    
    setTimeout(() => {
        // Mock license data - in a real app, this would come from the server
        const licenseData = {
            type: 'Professional',
            expiration: 'December 31, 2023',
            owner: 'John Doe (john.doe@example.com)',
            activeDevices: '2 of 3 allowed',
            projectExports: 'Unlimited',
            features: [
                { name: 'Video Exports', status: 'Enabled', details: 'Unlimited exports in up to 4K resolution' },
                { name: 'Advanced Effects', status: 'Enabled', details: 'Access to all premium effects and transitions' },
                { name: 'Commercial Usage', status: 'Enabled', details: 'Licensed for commercial projects' },
                { name: 'Batch Processing', status: 'Enabled', details: 'Process up to 10 videos simultaneously' },
                { name: 'Extended Analysis', status: 'Enabled', details: 'Access to advanced analytics and insights' },
                { name: 'API Access', status: 'Limited', details: '500 API calls per day (upgrade for more)' },
                { name: 'Sync Licensing', status: 'Enabled', details: 'Generate and export metadata for all tracks' },
                { name: 'Watermark Removal', status: 'Enabled', details: 'Remove Nova Sounds branding from exports' }
            ],
            history: [
                { date: 'Jan 15, 2023', action: 'License Purchased', details: 'Professional Plan - 1 Year' },
                { date: 'Jan 16, 2023', action: 'Device Activated', details: 'MacBook Pro (John\'s Laptop)' },
                { date: 'Mar 20, 2023', action: 'Device Activated', details: 'Mac Studio (Office)' },
                { date: 'Apr 10, 2023', action: 'License Feature Added', details: 'Added Batch Processing capability' }
            ],
            musicRights: [
                { track: 'Summer Vibes', license: 'Commercial', platforms: 'All Platforms' },
                { track: 'Urban Beats', license: 'Attribution', platforms: 'YouTube, TikTok' },
                { track: 'Cinematic Orchestra', license: 'Personal', platforms: 'Non-Commercial Only' }
            ],
            affiliateStats: {
                referrals: 0,
                earned: 0,
                commissionRate: '20%'
            }
        };
        
        // Update the UI with the license data
        document.getElementById('licenseType').textContent = licenseData.type;
        document.getElementById('licenseExpiration').textContent = licenseData.expiration;
        document.getElementById('licenseOwner').textContent = licenseData.owner;
        document.getElementById('activeDevices').textContent = licenseData.activeDevices;
        document.getElementById('projectExports').textContent = licenseData.projectExports;
        document.getElementById('licenseStatusMessage').textContent = `Your ${licenseData.type} license is active until ${licenseData.expiration}`;
    }, 1000);
}

// License renewal handler
function handleRenewLicense() {
    showLicenseModal('Renew Your License', 
        'Renew your Professional license for another year.',
        'Your current license expires on December 31, 2023. Renewing now will extend your license until December 31, 2024.',
        'Renew License - $199/year');
}

// License upgrade handler
function handleUpgradeLicense() {
    showLicenseModal('Upgrade Your License', 
        'Upgrade to an Enterprise license for more features.',
        'Upgrading to Enterprise gives you access to unlimited devices, priority support, and higher API limits.',
        'Upgrade to Enterprise - $499/year');
}

// License transfer handler
function handleTransferLicense() {
    showLicenseModal('Transfer Your License', 
        'Transfer your license to another user.',
        'This will remove the license from your account and transfer it to the specified email address.',
        'Transfer License',
        true);
}

// View all plans handler
function handleViewAllPlans() {
    window.location.href = '/pricing';
}

// Manage devices handler
function handleManageDevices() {
    showLicenseModal('Manage Active Devices', 
        'You have 2 of 3 allowed devices activated.',
        '<div class="list-group"><div class="list-group-item d-flex justify-content-between align-items-center">MacBook Pro (John\'s Laptop)<button class="btn btn-sm btn-outline-danger">Deactivate</button></div><div class="list-group-item d-flex justify-content-between align-items-center">Mac Studio (Office)<button class="btn btn-sm btn-outline-danger">Deactivate</button></div></div>',
        'Activate New Device');
}

// Import music rights handler
function handleImportMusicRights() {
    showLicenseModal('Import Rights Metadata',
        'Import track licensing information from CSV or JSON.',
        '<div class="mb-3"><label class="form-label">Select Import File</label><input type="file" class="form-control" accept=".csv,.json"></div><div class="form-check mb-3"><input class="form-check-input" type="checkbox" id="overwriteExisting" checked><label class="form-check-label" for="overwriteExisting">Overwrite existing entries</label></div>',
        'Import Metadata');
}

// Export music rights handler
function handleExportMusicRights() {
    showLicenseModal('Export Rights Database',
        'Export your track licensing information.',
        '<div class="mb-3"><label class="form-label">Export Format</label><select class="form-select"><option value="csv">CSV (Excel compatible)</option><option value="json">JSON</option></select></div><div class="form-check mb-3"><input class="form-check-input" type="checkbox" id="includeHistory"><label class="form-check-label" for="includeHistory">Include licensing history</label></div>',
        'Export Database');
}

// Manage license tags handler
function handleManageLicenseTags() {
    showLicenseModal('Manage License Tags',
        'Create and edit custom license tags.',
        '<div class="mb-3"><label class="form-label">Add New Tag</label><div class="input-group mb-3"><input type="text" class="form-control" placeholder="Tag name"><button class="btn btn-outline-primary" type="button">Add</button></div></div><div class="list-group mb-3"><div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">Commercial Use <div><button class="btn btn-sm btn-outline-primary me-1"><i class="bi bi-pencil"></i></button><button class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button></div></div><div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">Attribution Required <div><button class="btn btn-sm btn-outline-primary me-1"><i class="bi bi-pencil"></i></button><button class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button></div></div></div>',
        'Save Changes');
}

// Edit music rights handler
function handleEditMusicRights(trackName) {
    showLicenseModal('Edit Track Rights',
        `Update licensing information for "${trackName}"`,
        `<form>
            <div class="mb-3">
                <label class="form-label">License Type</label>
                <select class="form-select">
                    <option value="commercial">Commercial</option>
                    <option value="attribution">Attribution Required</option>
                    <option value="personal">Personal Use Only</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">Allowed Platforms</label>
                <div class="form-check mb-2">
                    <input class="form-check-input" type="checkbox" id="platformYouTube" checked>
                    <label class="form-check-label" for="platformYouTube">YouTube</label>
                </div>
                <div class="form-check mb-2">
                    <input class="form-check-input" type="checkbox" id="platformTikTok" checked>
                    <label class="form-check-label" for="platformTikTok">TikTok</label>
                </div>
                <div class="form-check mb-2">
                    <input class="form-check-input" type="checkbox" id="platformInstagram" checked>
                    <label class="form-check-label" for="platformInstagram">Instagram</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="platformFacebook" checked>
                    <label class="form-check-label" for="platformFacebook">Facebook</label>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label">Additional Notes</label>
                <textarea class="form-control" rows="2" placeholder="Any special terms or conditions"></textarea>
            </div>
        </form>`,
        'Update Rights');
}

// Affiliate system functions

// Function to load affiliate stats
async function loadAffiliateStats() {
    try {
        // Get the affiliate ID from local storage or from user data
        const affiliateId = localStorage.getItem('affiliateId') || userData?.affiliate_id;
        
        if (!affiliateId) {
            console.log('No affiliate ID found');
            return;
        }
        
        // Call API to get affiliate stats
        const response = await fetch(`/api/affiliate/stats/${affiliateId}`);
        if (!response.ok) throw new Error('Failed to fetch affiliate stats');
        
        const data = await response.json();
        
        // Update the UI with affiliate stats
        updateAffiliateUI(data);
        
        // Store the data for future reference
        userData.affiliateStats = data;
    } catch (error) {
        console.error('Error loading affiliate stats:', error);
    }
}

// Function to update affiliate UI
function updateAffiliateUI(data) {
    // Update referral count
    const referralCount = document.getElementById('referralCount');
    if (referralCount) {
        referralCount.textContent = data.total_referrals || 0;
    }
    
    // Update earnings
    const earningsValue = document.getElementById('earningsValue');
    if (earningsValue) {
        earningsValue.textContent = `$${data.total_earnings.toFixed(2)}`;
    }
    
    // Update conversion rate
    const conversionRate = document.getElementById('conversionRate');
    if (conversionRate) {
        conversionRate.textContent = `${data.conversion_rate.toFixed(1)}%`;
    }
    
    // Update referral link
    const referralLink = document.getElementById('referralLink');
    if (referralLink && data.referral_link) {
        referralLink.value = data.referral_link;
    }
}

// Function to track conversion (call when user makes a purchase)
function trackAffiliatePurchase(orderId, amount) {
    try {
        // Get the referral code from the URL or cookie
        const urlParams = new URLSearchParams(window.location.search);
        const referralCode = urlParams.get('ref') || getCookie('ref');
        
        if (!referralCode) {
            console.log('No referral code found');
            return;
        }
        
        // Track the conversion using Tapfiliate SDK
        tap('conversion', orderId, amount, {
            commission_type: 'percentage',
            commission_amount: 20 // 20% commission
        });
        
        // Also track in our backend
        fetch('/api/affiliate/conversion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                referral_code: referralCode,
                order_id: orderId,
                amount: amount
            })
        });
    } catch (error) {
        console.error('Error tracking affiliate purchase:', error);
    }
}

// Helper function to get cookie by name
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

// Copy referral link handler
function handleCopyReferralLink() {
    const referralLink = document.getElementById('referralLink');
    referralLink.select();
    document.execCommand('copy');
    
    showToast('Link Copied', 'Referral link copied to clipboard');
}

// Affiliate dashboard handler
function handleAffiliateDashboard() {
    window.location.href = '/affiliate-dashboard';
}

// Auto tag toggle handler
function handleAutoTagToggle() {
    const isChecked = document.getElementById('autoTagToggle').checked;
    
    // Show toast notification
    if (isChecked) {
        showToast('Auto-tagging Enabled', 'New tracks will be automatically tagged on import');
    } else {
        showToast('Auto-tagging Disabled', 'New tracks will need to be tagged manually');
    }
}

// Disable auto-renewal handler
function handleDisableAutoRenewal() {
    if (confirm('Are you sure you want to disable auto-renewal? Your license will expire on December 31, 2023 if not manually renewed.')) {
        // Simulate API call
        document.querySelector('#licenseStatusAlert').innerHTML = 
            '<i class="bi bi-info-circle me-2"></i><span>Auto-renewal has been disabled. Your license will expire on December 31, 2023.</span>';
        
        // Update button
        document.getElementById('disableAutoRenewalBtn').textContent = 'Enable Auto-Renewal';
        document.getElementById('disableAutoRenewalBtn').classList.remove('btn-outline-danger');
        document.getElementById('disableAutoRenewalBtn').classList.add('btn-outline-success');
        
        // Update the warning
        const alertElement = document.querySelector('.alert-warning');
        alertElement.classList.remove('alert-warning');
        alertElement.classList.add('alert-danger');
        alertElement.innerHTML = 
            '<i class="bi bi-exclamation-triangle me-2"></i><small>Auto-renewal is disabled. Your license will expire on December 31, 2023.</small>';
    }
}

// Update payment method handler
function handleUpdatePaymentMethod() {
    showLicenseModal('Update Payment Method', 
        'Update your billing information',
        '<form><div class="mb-3"><label class="form-label">Card Number</label><input type="text" class="form-control" placeholder="**** **** **** 1234"></div><div class="row"><div class="col-md-6"><div class="mb-3"><label class="form-label">Expiration Date</label><input type="text" class="form-control" placeholder="MM/YY"></div></div><div class="col-md-6"><div class="mb-3"><label class="form-label">CVC</label><input type="text" class="form-control" placeholder="123"></div></div></div><div class="mb-3"><label class="form-label">Billing Address</label><input type="text" class="form-control" placeholder="123 Main St"></div></form>',
        'Update Payment Method');
}

// Show modal for license operations
function showLicenseModal(title, subtitle, content, primaryButtonText, includeEmailField = false, hideMainButton = false) {
    // Check if modal already exists, remove if it does
    const existingModal = document.getElementById('licenseModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal fade" id="licenseModal" tabindex="-1" aria-labelledby="licenseModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="licenseModalLabel">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="lead">${subtitle}</p>
                        ${includeEmailField ? '<div class="mb-3"><label class="form-label">Email Address</label><input type="email" class="form-control" placeholder="recipient@example.com"></div>' : ''}
                        ${content}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        ${!hideMainButton ? `<button type="button" class="btn btn-primary" id="licenseModalActionBtn">${primaryButtonText}</button>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to the document
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Initialize modal
    const modal = new bootstrap.Modal(document.getElementById('licenseModal'));
    modal.show();
    
    // Add event listener for primary button
    const actionButton = document.getElementById('licenseModalActionBtn');
    if (actionButton) {
        actionButton.addEventListener('click', () => {
            // Simulate API action
            modal.hide();
            
            // Show success toast notification
            showToast(`${title} Successful`, 'Your request has been processed successfully.');
        });
    }
}

// Show toast notification
function showToast(title, message) {
    // Check if toast container exists, create if not
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast HTML
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <small>Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Add toast to container
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
    toast.show();
    
    // Remove toast after hiding
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
} 