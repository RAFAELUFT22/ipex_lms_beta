/**
 * Evolution API v2 - WhatsApp Group Management Helper
 * 
 * Provides a clean interface to interact with Evolution API v2 group endpoints.
 * 
 * Usage:
 * const evo = new EvolutionGroups(baseURL, apikey, instanceName);
 * await evo.createGroup("Group Name", ["5511999999999"], "Description");
 */

class EvolutionGroups {
    constructor(baseURL, apikey, instanceName) {
        // Priority: Passed URL > ENV > Internal Container Name > Fallback
        this.baseURL = baseURL || process.env.EVOLUTION_URL || "http://kreativ-evolution:8080";
        this.baseURL = this.baseURL.replace(/\/$/, "");
        this.apikey = apikey || process.env.EVOLUTION_API_KEY || "tds_evolution_key_50f5aacc";
        this.instanceName = instanceName || "kreativ-tds";
    }

    async _request(method, endpoint, body = null) {
        const url = `${this.baseURL}${endpoint.replace(':instanceName', this.instanceName)}`;
        const headers = {
            'apikey': this.apikey,
            'Content-Type': 'application/json'
        };

        const options = {
            method,
            headers
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: response.statusText }));
            throw new Error(`Evolution API Error [${response.status}]: ${error.message || JSON.stringify(error)}`);
        }
        return await response.json();
    }

    /**
     * 1. Create a Group
     */
    async createGroup(subject, participants, description = "", promoteParticipants = false) {
        return await this._request('POST', '/group/create/:instanceName', {
            subject,
            description,
            participants,
            promoteParticipants
        });
    }

    /**
     * 2. List Groups
     */
    async fetchAllGroups() {
        return await this._request('GET', '/group/fetchAllGroups/:instanceName');
    }

    /**
     * 3. Get Group Invite Code / Link
     */
    async getInviteCode(groupJid) {
        return await this._request('GET', `/group/inviteCode/:instanceName?groupJid=${groupJid}`);
    }

    /**
     * 4. Update Participants (Add, Remove, Promote, Demote)
     */
    async updateParticipants(groupJid, action, participants) {
        return await this._request('POST', '/group/updateParticipants/:instanceName', {
            groupJid,
            action,
            participants
        });
    }

    /**
     * 5. Send Invite Link via Message
     */
    async sendInvite(groupJid, numbers, description = "Join our learning group!") {
        return await this._request('POST', '/group/sendInvite/:instanceName', {
            groupJid,
            description,
            numbers
        });
    }
}

module.exports = EvolutionGroups;
